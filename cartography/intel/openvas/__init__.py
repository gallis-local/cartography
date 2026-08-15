"""
Cartography intel module for OpenVAS (Greenbone Vulnerability Management).

Syncs hosts, tasks (scans), targets, scan configs, schedules, port lists,
credentials, results (findings) and TLS certificates from a GVM instance via
the GMP protocol into the graph.
"""

import logging

import neo4j

import cartography.intel.openvas.findings
import cartography.intel.openvas.hosts
import cartography.intel.openvas.tasks
import cartography.intel.openvas.tls_certificates
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.openvas.api import gmp_session
from cartography.models.openvas.instance import OpenVASInstanceSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _get_instance_id(config: Config) -> str:
    """
    Derive the OpenVASInstance node id from the config.
    """
    if config.openvas_instance_id:
        return config.openvas_instance_id
    if config.openvas_socket_path:
        return f"unix:{config.openvas_socket_path}"
    return f"{config.openvas_host or 'localhost'}:{config.openvas_port}"


@timeit
def start_openvas_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Perform ingestion of OpenVAS data using the GMP protocol.
    :param neo4j_session: Neo4j session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.openvas_password:
        logger.info(
            "OpenVAS import is not configured - skipping this module. "
            "Set openvas_password to enable."
        )
        return

    instance_id = _get_instance_id(config)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "OPENVAS_INSTANCE_ID": instance_id,
    }

    load(
        neo4j_session,
        OpenVASInstanceSchema(),
        [
            {
                "id": instance_id,
                "name": instance_id,
                "host": config.openvas_host,
                "port": str(config.openvas_port),
                "user": config.openvas_user,
            },
        ],
        lastupdated=config.update_tag,
    )

    with gmp_session(config) as gmp:
        # Tasks and their supporting resources first so that host/results
        # relationship targets exist when those nodes are written.
        cartography.intel.openvas.tasks.sync_tasks_and_supporting(
            neo4j_session,
            gmp,
            instance_id,
            config.update_tag,
            common_job_parameters,
        )

        cartography.intel.openvas.hosts.sync_hosts(
            neo4j_session,
            gmp,
            instance_id,
            config.update_tag,
            common_job_parameters,
        )

        cartography.intel.openvas.findings.sync_results(
            neo4j_session,
            gmp,
            instance_id,
            config.update_tag,
            common_job_parameters,
            lookback_days=config.openvas_findings_lookback_days,
        )

        cartography.intel.openvas.tls_certificates.sync_tls_certificates(
            neo4j_session,
            gmp,
            instance_id,
            config.update_tag,
            common_job_parameters,
        )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="OpenVASInstance",
        group_id=instance_id,
        synced_type="OpenVASData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
