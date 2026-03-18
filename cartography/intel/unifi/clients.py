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
    logger.debug("Fetching UniFi clients")
    await controller.clients.update()

    # Get site_id from controller
    site_id = controller.connectivity.config.site

    # Convert aiounifi Client objects to dictionaries
    clients = []
    for client in controller.clients.values():
        # ap_mac is set for wireless clients only; sw_mac for wired clients only
        ap_mac = getattr(client, "ap_mac", None) or None

        # For wireless clients, find the switch the AP uplinks to.
        # Devices are synced before clients so controller.devices is populated.
        ap_switch_mac = None
        if ap_mac:
            ap_device = controller.devices.get(ap_mac)
            if ap_device:
                ap_uplink = ap_device.raw.get("uplink") or {}
                ap_switch_mac = ap_uplink.get("uplink_mac") or None

        # Build port_id for wired clients: "{sw_mac}_{sw_port}"
        sw_mac = client.switch_mac or None
        sw_port = client.switch_port
        port_id = f"{sw_mac}_{sw_port}" if sw_mac and sw_port is not None else None

        clients.append(
            {
                "mac": client.mac,
                "ip": getattr(client, "ip", None),
                "is_guest": getattr(client, "is_guest", False),
                "oui": getattr(client, "oui", None),
                "satisfaction": client.raw.get("satisfaction"),
                "channel": client.raw.get("channel"),
                "radio": client.raw.get("radio"),
                "is_wired": getattr(client, "is_wired", False),
                "qos_policy_applied": getattr(client, "qos_policy_applied", False),
                "ap_mac": ap_mac,
                "hostname": client.hostname or None,
                "name": client.name or None,
                "essid": client.essid or None,
                "blocked": client.blocked,
                "uptime": client.uptime,
                "last_seen": client.last_seen,
                "vlan": client.raw.get("vlan"),
                "sw_mac": sw_mac,
                "sw_port": sw_port,
                "port_id": port_id,
                "ap_switch_mac": ap_switch_mac,
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
