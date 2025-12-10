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
async def get(controller: Controller, site_id: str) -> list[dict[str, Any]]:
    """
    Retrieve UniFi devices from the controller.

    :param controller: Controller instance
    :param site_id: Site ID for the devices
    :return: List of device data
    """
    logger.info("Fetching UniFi devices")
    await controller.devices.update()

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
    return devices


@timeit
def load_devices(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load UniFi devices into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of device data
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi devices into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiDeviceSchema(),
        data,
        lastupdated=update_tag,
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
    site_id: str,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi devices.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param site_id: Site ID for the devices
    :param common_job_parameters: Common job parameters
    :return: List of device data
    """
    devices = await get(controller, site_id)
    load_devices(neo4j_session, devices, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return devices
