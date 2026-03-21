import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.wlan import UnifiWlanSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi WLANs from the controller.

    :param controller: Controller instance
    :return: List of WLAN data
    """
    logger.debug("Fetching UniFi WLANs")
    await controller.wlans.update()

    # Convert aiounifi WLAN objects to dictionaries
    wlans = []
    for wlan in controller.wlans.values():
        wlans.append(
            {
                "id": wlan.id,
                "name": wlan.name,
                "enabled": wlan.enabled,
                "is_guest": wlan.is_guest,
                "security": wlan.raw.get("security"),
                "wpa_mode": wlan.raw.get("wpa_mode"),
                "wpa_enc": wlan.raw.get("wpa_enc"),
                "usergroup_id": wlan.raw.get("usergroup_id"),
                "hide_ssid": wlan.hide_ssid,
                "mac_filter_enabled": wlan.mac_filter_enabled,
                "mac_filter_policy": wlan.raw.get("mac_filter_policy"),
                "bc_filter_enabled": wlan.bc_filter_enabled,
                "no2ghz_oui": wlan.raw.get("no2ghz_oui"),
                "name_combine_enabled": wlan.name_combine_enabled,
                "wlangroup_id": wlan.raw.get("wlangroup_id"),
                "schedule": wlan.raw.get("schedule"),
            }
        )
    logger.debug("Fetched %d UniFi WLANs", len(wlans))
    return wlans


@timeit
def load_wlans(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi WLANs into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of WLAN data
    :param site_id: Site ID for the WLANs
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi WLANs to the graph.", len(data))
    load(
        neo4j_session,
        UnifiWlanSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi WLANs from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi WLAN cleanup job")
    GraphJob.from_node_schema(UnifiWlanSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi WLANs.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    wlans = await get(controller)
    load_wlans(neo4j_session, wlans, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
