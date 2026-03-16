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
    logger.info("Fetching UniFi ports")
    await controller.ports.update()

    # Get site_id from controller
    site_id = controller.connectivity.site_id

    # Convert aiounifi Port objects to dictionaries
    ports = []
    for port in controller.ports.values():
        # Create unique ID from device_mac and port_idx
        port_id = f"{port.device_mac}:{port.port_idx}"

        ports.append(
            {
                "id": port_id,
                "port_idx": port.port_idx,
                "name": getattr(port, "name", f"Port {port.port_idx}"),
                "port_poe": getattr(port, "port_poe", False),
                "poe_enable": getattr(port, "poe_enable", False),
                "poe_mode": getattr(port, "poe_mode", None),
                "poe_voltage": getattr(port, "poe_voltage", None),
                "portconf_id": getattr(port, "portconf_id", None),
                "up": getattr(port, "up", False),
                "speed": getattr(port, "speed", 0),
                "full_duplex": getattr(port, "full_duplex", False),
                "device_mac": port.device_mac,
                "site_id": site_id,
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
    logger.info("Loading %d UniFi ports into Neo4j.", len(data))
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
    cleanup_params = {**common_job_parameters, "site_id": site_id}
    cleanup(neo4j_session, cleanup_params)
    return ports
