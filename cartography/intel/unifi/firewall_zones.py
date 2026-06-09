import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.firewall_zone import UnifiFirewallZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi firewall zones from the controller.

    :param controller: Controller instance
    :return: List of firewall zone data
    """
    logger.debug("Fetching UniFi firewall zones")
    await controller.firewall_zones.update()
    zones = []
    for zone in controller.firewall_zones.values():
        zones.append(
            {
                "id": zone.id,
                "name": zone.name,
                "attr_no_edit": zone.raw.get("attr_no_edit", False),
                "default_zone": zone.raw.get("default_zone", False),
                "zone_key": zone.raw.get("zone_key"),
                "network_ids": zone.raw.get("network_ids"),
            }
        )
    logger.debug("Fetched %d UniFi firewall zones", len(zones))
    return zones


@timeit
def load_firewall_zones(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi firewall zones into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of firewall zone data
    :param site_id: Site ID for the firewall zones
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi firewall zones to the graph.", len(data))
    load(
        neo4j_session,
        UnifiFirewallZoneSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi firewall zones from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi firewall zone cleanup job")
    GraphJob.from_node_schema(UnifiFirewallZoneSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi firewall zones.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    zones = await get(controller)
    load_firewall_zones(
        neo4j_session, zones, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
