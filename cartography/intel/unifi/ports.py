import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.port import UnifiPortSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> tuple[list[dict[str, Any]], str]:
    """
    Retrieve UniFi ports from the controller.

    :param controller: Controller instance
    :return: Tuple of (List of port data, site_id)
    """
    logger.debug("Fetching UniFi ports")
    # Ports are populated via device subscription when controller.devices.update()
    # is called — no separate API request needed for ports.

    # Get site_id from controller
    site_id = controller.connectivity.config.site

    # Convert aiounifi Port objects to dictionaries
    # Ports are keyed as "{device_id}_{port_idx}" in controller.ports
    ports = []
    for obj_id, port in controller.ports.items():
        # Extract device_mac from the key (format: "{device_mac}_{port_idx}")
        device_mac = obj_id.rsplit("_", 1)[0]

        ports.append(
            {
                "id": obj_id,
                "port_idx": port.port_idx,
                "name": port.name,
                "port_poe": port.port_poe,
                "poe_enable": port.poe_enable,
                "poe_mode": port.poe_mode,
                "poe_voltage": port.poe_voltage,
                "portconf_id": port.portconf_id,
                "up": port.up,
                "speed": port.raw.get("speed", 0),
                "full_duplex": port.raw.get("full_duplex", False),
                "device_mac": device_mac,
            }
        )
    return ports, site_id


@timeit
def load_ports(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi ports into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of port data
    :param site_id: Site ID for the ports
    :param update_tag: Update tag for the sync
    """
    load(
        neo4j_session,
        UnifiPortSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi ports from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiPortSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi ports.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    :return: List of port data
    """
    ports, site_id = await get(controller)
    load_ports(neo4j_session, ports, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return ports
