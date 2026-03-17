import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.traffic_route import UnifiTrafficRouteSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller, site_id: str) -> list[dict[str, Any]]:
    """
    Retrieve UniFi traffic routes from the controller.

    :param controller: Controller instance
    :param site_id: Site ID for the traffic routes
    :return: List of traffic route data
    """
    logger.info("Fetching UniFi traffic routes")
    await controller.traffic_routes.update()

    # Convert aiounifi TrafficRoute objects to dictionaries
    traffic_routes = []
    for route in controller.traffic_routes.values():
        # Extract domain name strings from the domains list of Domain objects
        domain_names = [
            d["domain"] for d in (route.raw.get("domains") or []) if d.get("domain")
        ]
        # Extract client MACs from target_devices
        target_client_macs = [
            td["client_mac"]
            for td in (route.raw.get("target_devices") or [])
            if td.get("client_mac")
        ]
        traffic_routes.append(
            {
                "id": route.id,
                "description": route.description,
                "enabled": route.enabled,
                "matching_target": str(route.matching_target),
                "network_id": route.network_id,
                "next_hop": route.next_hop,
                "regions": route.raw.get("regions") or None,
                "domains": domain_names or None,
                "target_client_macs": target_client_macs or None,
                "site_id": site_id,
            }
        )
    return traffic_routes


@timeit
def load_traffic_routes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi traffic routes into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of traffic route data
    :param site_id: Site ID for the traffic routes
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi traffic routes into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiTrafficRouteSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi traffic routes from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiTrafficRouteSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    site_id: str,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi traffic routes.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param site_id: Site ID for the traffic routes
    :param common_job_parameters: Common job parameters
    :return: List of traffic route data
    """
    traffic_routes = await get(controller, site_id)
    load_traffic_routes(
        neo4j_session, traffic_routes, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup_params = {**common_job_parameters, "site_id": site_id}
    cleanup(neo4j_session, cleanup_params)
    return traffic_routes
