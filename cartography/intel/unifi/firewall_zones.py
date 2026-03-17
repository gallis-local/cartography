import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.firewall_zone import UnifiFirewallZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Any, site_id: str) -> list[dict[str, Any]]:
    """
    Get firewall zones from UniFi controller
    """
    await controller.firewall_zones.update()
    zones = []
    for zone in controller.firewall_zones.values():
        zones.append(
            {
                "id": zone.id,
                "name": zone.name,
                "attr_no_edit": zone.raw.get("attr_no_edit", False),
                "default_zone": zone.raw.get("default_zone", False),
                "zone_key": zone.raw.get("zone_key", ""),
                "network_ids": zone.raw.get("network_ids", []),
            }
        )
    return zones


@timeit
def load_firewall_zones(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load firewall zones into the graph
    """
    load(
        neo4j_session,
        UnifiFirewallZoneSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Remove firewall zones that were not updated in this run
    """
    logger.debug("Running UniFi firewall zone cleanup job")
    GraphJob.from_node_schema(UnifiFirewallZoneSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Any,
    site_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync firewall zones from UniFi controller to Neo4j
    """
    zones = await get(controller, site_id)
    load_firewall_zones(neo4j_session, zones, site_id, update_tag)
    cleanup(neo4j_session, {**common_job_parameters, "site_id": site_id})
