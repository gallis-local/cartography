import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.client import UnifiClientSchema
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi clients from the controller.

    :param controller: Controller instance
    :return: List of client data
    """
    logger.debug("Fetching UniFi clients")
    await controller.clients.update()

    # Convert aiounifi Client objects to dictionaries
    clients = []
    for client in controller.clients.values():
        # access_point_mac is set for wireless clients only; sw_mac for wired clients only
        ap_mac = client.access_point_mac or None

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
                "qos_policy_applied": client.raw.get("qos_policy_applied", False),
                "ap_mac": ap_mac,
                "hostname": client.hostname or None,
                "name": client.name or None,
                "essid": client.essid or None,
                "wlanconf_id": client.raw.get("wlanconf_id"),
                "blocked": client.blocked,
                "uptime": client.uptime,
                "last_seen": client.last_seen,
                "vlan": client.raw.get("vlan"),
                "sw_mac": sw_mac,
                "sw_port": sw_port,
                "port_id": port_id,
                "ap_switch_mac": ap_switch_mac,
                # Security-relevant properties
                "first_seen": client.raw.get("first_seen"),
                "fixed_ip": client.raw.get("fixed_ip"),
                "idle_time": client.raw.get("idletime"),
                "latest_association_time": client.raw.get("latest_assoc_time"),
                "rx_bytes": client.raw.get("rx_bytes"),
                "rx_bytes_r": client.raw.get("rx_bytes-r"),
                "tx_bytes": client.raw.get("tx_bytes"),
                "tx_bytes_r": client.raw.get("tx_bytes-r"),
                "wired_rx_bytes": client.raw.get("wired-rx_bytes"),
                "wired_rx_bytes_r": client.raw.get("wired-rx_bytes-r"),
                "wired_tx_bytes": client.raw.get("wired-tx_bytes"),
                "wired_tx_bytes_r": client.raw.get("wired-tx_bytes-r"),
                "wired_rate_mbps": client.raw.get("wired_rate_mbps"),
                "uptime_by_access_point": client.raw.get("_uptime_by_uap"),
                "uptime_by_gateway": client.raw.get("_uptime_by_ugw"),
                "uptime_by_switch": client.raw.get("_uptime_by_usw"),
                "switch_depth": client.raw.get("sw_depth"),
                "powersave_enabled": client.raw.get("powersave_enabled"),
                "device_name": client.raw.get("device_name"),
                "firmware_version": client.raw.get("fw_version"),
                "association_time": client.raw.get("assoc_time"),
                "last_seen_by_access_point": client.raw.get("_last_seen_by_uap"),
                "last_seen_by_gateway": client.raw.get("_last_seen_by_ugw"),
                "last_seen_by_switch": client.raw.get("_last_seen_by_usw"),
            }
        )
    logger.debug("Fetched %d UniFi clients", len(clients))
    return clients


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
    logger.debug("Loading %d UniFi clients to the graph.", len(data))
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
    logger.debug("Running UniFi client cleanup job")
    GraphJob.from_node_schema(UnifiClientSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi clients.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    clients = await get(controller)
    load_clients(neo4j_session, clients, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)

    stat_handler.incr("unifi_clients_synced", len(clients))
