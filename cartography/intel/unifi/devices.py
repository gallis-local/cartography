import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.device import UnifiDeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> tuple[list[dict[str, Any]], str]:
    """
    Retrieve UniFi devices from the controller.

    :param controller: Controller instance
    :return: Tuple of (List of device data, site_id)
    """
    logger.info("Fetching UniFi devices")
    await controller.devices.update()

    # Get site_id from controller
    site_id = controller.connectivity.site_id

    # Convert aiounifi Device objects to dictionaries
    devices = []
    for device in controller.devices.values():
        devices.append(
            {
                "mac": device.mac,
                "adopted": device.adopted,
                "type": device.type,
                "model": device.model,
                "name": device.name or device.mac,  # Fallback to MAC if no name
                "site_id": site_id,
            }
        )
    return devices, site_id


@timeit
def load_devices(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi devices into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of device data
    :param site_id: Site ID for the devices
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi devices into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiDeviceSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi devices from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiDeviceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi devices.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    :return: List of device data
    """
    devices, site_id = await get(controller)
    load_devices(neo4j_session, devices, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup_params = {**common_job_parameters, "site_id": site_id}
    cleanup(neo4j_session, cleanup_params)
    return devices
