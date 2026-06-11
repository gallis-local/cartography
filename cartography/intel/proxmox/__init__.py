"""
Proxmox Virtual Environment intelligence module for Cartography.

This module syncs Proxmox infrastructure including clusters, nodes, VMs,
containers, storage, networks, users, and backup configurations.
"""

import backoff
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
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job
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
            timeout=config.proxmox_timeout,
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
            timeout=config.proxmox_timeout,
        )

    else:
        raise ValueError("No Proxmox authentication method configured")


def _proxmox_retry_predicate(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.

    Retries on: connection errors, timeouts, 5xx errors, rate limiting.
    Does not retry on: 4xx errors (except 429), auth failures.
    """
    error_str = str(exception).lower()
    # Connection/timeout errors
    if any(
        err in error_str
        for err in [
            "connection",
            "timeout",
            "timed out",
            "unreachable",
            "refused",
            "reset",
            "broken pipe",
        ]
    ):
        return True
    # HTTP status codes that warrant retry
    if any(
        code in error_str
        for code in [
            "500",
            "502",
            "503",
            "504",
            "429",
        ]
    ):
        return True
    # Specific proxmoxer exception types
    if "proxmoxer" in str(type(exception)).lower():
        return True
    return False


def _with_proxmox_retry(config: Config):
    """
    Decorator factory that applies retry logic with exponential backoff.

    Uses config.proxmox_max_retries and config.proxmox_retry_backoff.
    """
    return backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=config.proxmox_max_retries,
        factor=config.proxmox_retry_backoff,
        giveup=lambda e: not _proxmox_retry_predicate(e),
        on_backoff=lambda details: logger.warning(
            f"Proxmox API call failed: {details.get('exception', 'unknown')}. "
            f"Retrying in {details.get('wait', 0):.1f}s (attempt {details.get('tries', 0)}/{config.proxmox_max_retries})"
        ),
    )


def _best_effort_wrapper(config: Config, func, *args, **kwargs):
    """
    Wrapper that logs errors instead of raising if best-effort mode is enabled.

    :param config: Cartography configuration object
    :param func: Function to wrap
    :param args: Positional arguments for func
    :param kwargs: Keyword arguments for func
    :return: Result of func or None if error occurred in best-effort mode
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if config.proxmox_best_effort_mode:
            logger.error(
                f"Proxmox sync error in {func.__name__} (best-effort mode): {e}"
            )
            return None
        raise


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
    cluster_data = _best_effort_wrapper(
        config,
        cluster.sync,
        neo4j_session,
        proxmox_client,
        config.proxmox_host,
        config.update_tag,
        common_job_parameters,
    )
    if cluster_data is None:
        logger.error("Cluster sync failed, cannot continue without cluster_id")
        return

    cluster_id = cluster_data["cluster_id"]

    # Add cluster_id to common_job_parameters for cleanup jobs
    common_job_parameters["CLUSTER_ID"] = cluster_id

    # Sync SDN (Software-Defined Networking) resources
    _best_effort_wrapper(
        config,
        sdn.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync storage first — required by compute (STORED_ON) and pool (CONTAINS_STORAGE)
    _best_effort_wrapper(
        config,
        storage.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync VMs and containers
    vms = _best_effort_wrapper(
        config,
        compute.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
        enable_guest_agent=config.proxmox_enable_guest_agent,
    )

    # Sync VM and container snapshots
    _best_effort_wrapper(
        config,
        snapshot.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
        vms,
    )

    # Sync resource pools
    _best_effort_wrapper(
        config,
        pool.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync backup jobs
    _best_effort_wrapper(
        config,
        backup.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync replication jobs
    _best_effort_wrapper(
        config,
        replication.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync HA groups and resources
    _best_effort_wrapper(
        config,
        ha.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync authentication realms first (users reference realms via AUTHENTICATES_VIA)
    _best_effort_wrapper(
        config,
        authrealm.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync access control (users, groups, roles, ACLs)
    users = _best_effort_wrapper(
        config,
        access.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync API tokens for users
    _best_effort_wrapper(
        config,
        apitoken.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
        users,
    )

    # Sync firewall rules and IP sets
    _best_effort_wrapper(
        config,
        firewall.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync firewall global options
    _best_effort_wrapper(
        config,
        firewalloptions.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync SSL/TLS certificates
    _best_effort_wrapper(
        config,
        certificate.sync,
        neo4j_session,
        proxmox_client,
        cluster_id,
        config.update_tag,
        common_job_parameters,
    )

    # Run post-ingestion analysis: create derived relationships
    _best_effort_wrapper(
        config,
        analysis.run_effective_permissions,
        neo4j_session,
        config.update_tag,
        cluster_id,
    )
    _best_effort_wrapper(
        config,
        analysis.run_has_role_relationships,
        neo4j_session,
        config.update_tag,
        cluster_id,
    )

    # Run ontology linking: connect Proxmox nodes to canonical ontology nodes
    run_analysis_job(
        "proxmox_ontology_linking.json",
        neo4j_session,
        common_job_parameters,
    )

    # Run Proxmox-specific analysis jobs
    run_analysis_job(
        "proxmox_backup_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
    run_analysis_job(
        "proxmox_replication_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
    run_analysis_job(
        "proxmox_ha_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
    run_analysis_job(
        "proxmox_certificate_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
    run_analysis_job(
        "proxmox_guest_agent_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
    run_analysis_job(
        "proxmox_storage_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
    run_analysis_job(
        "proxmox_security.json",
        neo4j_session,
        common_job_parameters,
    )

    # Run centralized cleanup job to remove stale cross-module resources
    run_cleanup_job(
        "proxmox_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="ProxmoxCluster",
        group_id=cluster_id,
        synced_type="ProxmoxCluster",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

    logger.info("Completed Proxmox infrastructure sync")
