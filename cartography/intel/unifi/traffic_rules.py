import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.traffic_rule import UnifiTrafficRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller, site_id: str) -> list[dict[str, Any]]:
    """
    Retrieve UniFi traffic rules from the controller.

    :param controller: Controller instance
    :param site_id: Site ID for the traffic rules
    :return: List of traffic rule data
    """
    logger.info("Fetching UniFi traffic rules")
    await controller.traffic_rules.update()

    # Convert aiounifi TrafficRule objects to dictionaries
    traffic_rules = []
    for rule in controller.traffic_rules.values():
        traffic_rules.append(
            {
                "id": rule.id,
                "description": rule.description,
                "enabled": rule.enabled,
                "action": rule.action,
                "matching_target": rule.matching_target,
                # Bandwidth limit settings
                "bandwidth_limit_enabled": rule.raw.get("bandwidth_limit", {}).get("enabled", False),
                "download_limit_kbps": rule.raw.get("bandwidth_limit", {}).get("download_limit_kbps"),
                "upload_limit_kbps": rule.raw.get("bandwidth_limit", {}).get("upload_limit_kbps"),
                "site_id": site_id,
            }
        )
    return traffic_rules


@timeit
def load_traffic_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load UniFi traffic rules into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of traffic rule data
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi traffic rules into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiTrafficRuleSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi traffic rules from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiTrafficRuleSchema(), common_job_parameters).run(
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
    Sync UniFi traffic rules.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param site_id: Site ID for the traffic rules
    :param common_job_parameters: Common job parameters
    :return: List of traffic rule data
    """
    traffic_rules = await get(controller, site_id)
    load_traffic_rules(neo4j_session, traffic_rules, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return traffic_rules
