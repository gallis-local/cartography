import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.outlet import UnifiOutletSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi outlets from the controller.

    Outlets are populated via device subscription when controller.devices.update()
    is called — no separate API request needed for outlets.

    :param controller: Controller instance
    :return: List of outlet data
    """
    logger.debug("Fetching UniFi outlets")

    # Convert aiounifi Outlet objects to dictionaries
    # Outlets are keyed as "{device_id}_{index}" in controller.outlets
    outlets = []
    for obj_id, outlet in controller.outlets.items():
        # Extract device_mac from the key (format: "{device_mac}_{index}")
        device_mac = obj_id.rsplit("_", 1)[0]

        outlets.append(
            {
                "id": obj_id,
                "name": outlet.name,
                "index": outlet.index,
                "has_relay": outlet.has_relay,
                "relay_state": outlet.relay_state,
                "cycle_enabled": outlet.cycle_enabled,
                "has_metering": outlet.has_metering,
                "caps": outlet.caps,
                "voltage": outlet.voltage,
                "current": outlet.current,
                "power": outlet.power,
                "power_factor": outlet.power_factor,
                "device_mac": device_mac,
            }
        )
    logger.debug("Fetched %d UniFi outlets", len(outlets))
    return outlets


@timeit
def load_outlets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi outlets into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of outlet data
    :param site_id: Site ID for the outlets
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi outlets to the graph.", len(data))
    load(
        neo4j_session,
        UnifiOutletSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi outlets from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi outlet cleanup job")
    GraphJob.from_node_schema(UnifiOutletSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi outlets.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    outlets = await get(controller)
    load_outlets(neo4j_session, outlets, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
