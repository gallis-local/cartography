import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.client import UnifiClientSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> tuple[list[dict[str, Any]], str]:
    """
    Retrieve UniFi clients from the controller.

    :param controller: Controller instance
    :return: Tuple of (List of client data, site_id)
    """
    logger.info("Fetching UniFi clients")
    await controller.clients.update()

    # Get site_id from controller
    site_id = controller.connectivity.site_id

    # Convert aiounifi Client objects to dictionaries
    clients = []
    for client in controller.clients.values():
        # Get the AP MAC address from the client's device association
        ap_mac = getattr(client, "ap_mac", None) or getattr(client, "sw_mac", None)

        clients.append(
            {
                "mac": client.mac,
                "ip": getattr(client, "ip", None),
                "is_guest": getattr(client, "is_guest", False),
                "oui": getattr(client, "oui", None),
                "satisfaction": getattr(client, "satisfaction", None),
                "channel": getattr(client, "channel", None),
                "radio": getattr(client, "radio", None),
                "is_wired": getattr(client, "is_wired", False),
                "qos_policy_applied": getattr(client, "qos_policy_applied", False),
                "ap_mac": ap_mac,
                "site_id": site_id,
            }
        )
    return clients, site_id


@timeit
def load_clients(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi clients into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of client data
    :param site_id: Site ID for the clients
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi clients into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiClientSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi clients from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiClientSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi clients.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    :return: List of client data
    """
    clients, site_id = await get(controller)
    load_clients(neo4j_session, clients, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup_params = {**common_job_parameters, "site_id": site_id}
    cleanup(neo4j_session, cleanup_params)
    return clients
