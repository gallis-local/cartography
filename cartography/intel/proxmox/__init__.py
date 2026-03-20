"""
Proxmox Virtual Environment intelligence module for Cartography.

This module syncs Proxmox infrastructure including clusters, nodes, VMs,
containers, storage, networks, users, and backup configurations.
"""

import logging
import os
from typing import TYPE_CHECKING

import neo4j

if TYPE_CHECKING:
    from proxmoxer import ProxmoxAPI

from cartography.config import Config
from cartography.intel.proxmox import access
from cartography.intel.proxmox import analysis
from cartography.intel.proxmox import apitoken
from cartography.intel.proxmox import authrealm
from cartography.intel.proxmox import backup
from cartography.intel.proxmox import certificate
from cartography.intel.proxmox import cluster
from cartography.intel.proxmox import compute
from cartography.intel.proxmox import firewall
from cartography.intel.proxmox import firewalloptions
from cartography.intel.proxmox import ha
from cartography.intel.proxmox import pool
from cartography.intel.proxmox import replication
from cartography.intel.proxmox import sdn
from cartography.intel.proxmox import snapshot
from cartography.intel.proxmox import storage
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _get_proxmox_client(config: Config) -> "ProxmoxAPI":
    """
    Create and return a Proxmox API client.

    :param config: Cartography configuration object
    :return: ProxmoxAPI client
    :raises: ValueError if credentials not found in environment or proxmoxer not installed
    """
    try:
        from proxmoxer import ProxmoxAPI
    except ImportError:
        raise ImportError(
            "The proxmoxer library is required for Proxmox sync. "
            "Install it with: pip install proxmoxer"
        )

    host = config.proxmox_host
    port = config.proxmox_port
    user = config.proxmox_user
    verify_ssl = config.proxmox_verify_ssl

    # Try token-based auth first (recommended)
    if config.proxmox_token_name_env_var and config.proxmox_token_value_env_var:
        token_name = os.environ.get(config.proxmox_token_name_env_var)
        token_value = os.environ.get(config.proxmox_token_value_env_var)

        if not token_name:
            raise ValueError(
                f"Environment variable {config.proxmox_token_name_env_var} "
                f"not found or is empty"
            )
        if not token_value:
            raise ValueError(
                f"Environment variable {config.proxmox_token_value_env_var} "
                f"not found or is empty"
            )

        logger.info(f"Connecting to Proxmox at {host} using API token")
        return ProxmoxAPI(
            host,
            port=port,
            user=user,
            token_name=token_name,
            token_value=token_value,
            verify_ssl=verify_ssl,
        )

    # Fall back to password auth
    elif config.proxmox_password_env_var:
        password = os.environ.get(config.proxmox_password_env_var)

        if not password:
            raise ValueError(
                f"Environment variable {config.proxmox_password_env_var} "
                f"not found or is empty"
            )

        logger.info(f"Connecting to Proxmox at {host} using password auth")
        return ProxmoxAPI(
            host,
            port=port,
            user=user,
            password=password,
            verify_ssl=verify_ssl,
        )

    else:
        raise ValueError("No Proxmox authentication method configured")


@timeit
def start_proxmox_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Main entry point for Proxmox data ingestion.

    This is the primary sync function called by Cartography's sync orchestrator.

    :param neo4j_session: Neo4j session for database operations
    :param config: Cartography configuration object
    """
    if not config.proxmox_host:
        logger.info("Proxmox host not configured, skipping Proxmox sync")
        return

    logger.info(f"Starting Proxmox infrastructure sync for {config.proxmox_host}")

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Get Proxmox API client
    proxmox_client = _get_proxmox_client(config)

    # Sync cluster and nodes (returns cluster_id for other modules)
    cluster_data = cluster.sync(
        neo4j_session,
        proxmox_client,
        config.proxmox_host,
        config.update_tag,
        common_job_parameters,
    )

    cluster_id = cluster_data["cluster_id"]

    # Add cluster_id to common_job_parameters for cleanup jobs
    common_job_parameters["CLUSTER_ID"] = cluster_id

    # Sync SDN (Software-Defined Networking) resources
    sdn.sync_sdn(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync storage first — required by compute (STORED_ON) and pool (CONTAINS_STORAGE)
    storage.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync VMs and containers
    vms = compute.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
        enable_guest_agent=config.proxmox_enable_guest_agent,
    )

    # Sync VM and container snapshots
    snapshot.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
        vms,
    )

    # Sync resource pools
    pool.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync backup jobs
    backup.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync replication jobs
    replication.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync HA groups and resources
    ha.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync authentication realms first (users reference realms via AUTHENTICATES_VIA)
    authrealm.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync access control (users, groups, roles, ACLs)
    users = access.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync API tokens for users
    apitoken.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
        users,
    )

    # Sync firewall rules and IP sets
    firewall.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync firewall global options
    firewalloptions.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync SSL/TLS certificates
    certificate.sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Run post-ingestion analysis: create derived HAS_PERMISSION relationships
    analysis.run_effective_permissions(neo4j_session, config.update_tag, cluster_id)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="ProxmoxCluster",
        group_id=cluster_id,
        synced_type="ProxmoxCluster",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

    logger.info("Completed Proxmox infrastructure sync")
