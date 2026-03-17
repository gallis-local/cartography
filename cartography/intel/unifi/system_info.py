import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.system_info import UnifiSystemInfoSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Any) -> list[dict[str, Any]]:
    """
    Get system information from UniFi controller
    """
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
    return system_info


@timeit
def load_system_info(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load system information into the graph
    """
    load(
        neo4j_session,
        UnifiSystemInfoSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Remove system information that was not updated in this run
    """
    logger.debug("Running UniFi system info cleanup job")
    GraphJob.from_node_schema(UnifiSystemInfoSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Any,
    site_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync system information from UniFi controller to Neo4j
    """
    system_info = await get(controller)
    load_system_info(neo4j_session, system_info, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, {**common_job_parameters, "site_id": site_id})
