import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller
from aiounifi.models.device import DeviceState

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.device import UnifiDeviceSchema
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi devices from the controller.

    :param controller: Controller instance
    :return: List of device data
    """
    logger.debug("Fetching UniFi devices")
    await controller.devices.update()

    # Convert aiounifi Device objects to dictionaries
    devices = []
    for device in controller.devices.values():
        state_val = device.raw.get("state")
        uplink = device.raw.get("uplink") or {}

        # Collect broadcast WLAN IDs from vap_table (active broadcasts) and
        # wlan_overrides (configured per-radio overrides), deduplicating across both.
        wlan_id_set: set[str] = set()
        for vap in device.raw.get("vap_table") or []:
            wlan_conf_id = vap.get("wlanconf_id") or vap.get("wlan_id")
            if wlan_conf_id:
                wlan_id_set.add(wlan_conf_id)
        for override in device.wlan_overrides:
            wlan_id = override.get("wlan_id")
            if wlan_id:
                wlan_id_set.add(wlan_id)

        devices.append(
            {
                "mac": device.mac,
                "adopted": device.raw.get("adopted", False),
                "type": device.type,
                "model": device.model,
                "name": device.name or device.mac,  # Fallback to MAC if no name
                "ip": device.ip,
                "version": device.raw.get("version"),
                "state": (
                    DeviceState(state_val).name
                    if state_val in DeviceState._value2member_map_
                    else (str(state_val) if state_val is not None else None)
                ),
                "uptime": device.uptime,
                "last_seen": device.last_seen,
                "upgradable": device.upgradable,
                "uplink_mac": uplink.get("uplink_mac"),
                "uplink_port_id": (
                    f"{uplink['uplink_mac']}_{uplink['uplink_remote_port']}"
                    if uplink.get("uplink_mac")
                    and uplink.get("uplink_remote_port") is not None
                    else None
                ),
                "wlan_ids": list(wlan_id_set) or None,
                # Security-relevant properties
                "last_wan_ip": device.raw.get("last_wan_ip"),
                "uplink_depth": device.raw.get("uplink_depth"),
                "user_num_sta": device.raw.get("user-num_sta"),
                "overheating": device.raw.get("overheating", False),
                "upgrade_to_firmware": device.raw.get("upgrade_to_firmware"),
                "outlet_ac_power_budget": device.raw.get("outlet_ac_power_budget"),
                "outlet_ac_power_consumption": device.raw.get(
                    "outlet_ac_power_consumption"
                ),
            }
        )
    logger.debug("Fetched %d UniFi devices", len(devices))
    return devices


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
    logger.debug("Loading %d UniFi devices to the graph.", len(data))
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
    logger.debug("Running UniFi device cleanup job")
    GraphJob.from_node_schema(UnifiDeviceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi devices.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    devices = await get(controller)
    load_devices(neo4j_session, devices, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)

    stat_handler.incr("unifi_devices_synced", len(devices))
