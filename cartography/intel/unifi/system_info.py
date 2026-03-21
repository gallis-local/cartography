import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.system_info import UnifiSystemInfoSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve system information from the UniFi controller.

    :param controller: Controller instance
    :return: List of system info data
    """
    logger.debug("Fetching UniFi system information")
    await controller.system_information.update()
    system_info = []
    for info in controller.system_information.values():
        system_info.append(
            {
                "id": info.anonymous_controller_id,
                "anonymous_controller_id": info.anonymous_controller_id,
                "hostname": info.hostname,
                "name": info.name,
                "version": info.version,
                "previous_version": info.previous_version,
                "update_available": info.update_available,
                "ip_addrs": info.ip_address,
                "is_cloud_console": info.is_cloud_console,
                "ubnt_device_type": info.device_type,
            }
        )
    logger.debug("Fetched %d UniFi system info", len(system_info))
    return system_info


@timeit
def load_system_info(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi system information into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of system info data
    :param site_id: Site ID for the system info
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi system info records to the graph.", len(data))
    load(
        neo4j_session,
        UnifiSystemInfoSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi system information from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi system info cleanup job")
    GraphJob.from_node_schema(UnifiSystemInfoSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi system information.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    system_info = await get(controller)
    load_system_info(neo4j_session, system_info, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
