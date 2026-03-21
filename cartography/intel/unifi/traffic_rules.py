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
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi traffic rules from the controller.

    :param controller: Controller instance
    :return: List of traffic rule data
    """
    logger.debug("Fetching UniFi traffic rules")
    await controller.traffic_rules.update()

    # Convert aiounifi TrafficRule objects to dictionaries
    traffic_rules = []
    for rule in controller.traffic_rules.values():
        bw_limit = rule.raw.get("bandwidth_limit", {}) or {}
        # Extract client MACs from target_devices
        target_client_macs = [
            td["client_mac"]
            for td in (rule.raw.get("target_devices") or [])
            if td.get("client_mac")
        ]
        traffic_rules.append(
            {
                "id": rule.id,
                "description": rule.description,
                "enabled": rule.enabled,
                "action": rule.action,
                "matching_target": rule.matching_target,
                # Bandwidth limit settings
                "bandwidth_limit_enabled": bw_limit.get("enabled", False),
                "download_limit_kbps": bw_limit.get("download_limit_kbps"),
                "upload_limit_kbps": bw_limit.get("upload_limit_kbps"),
                # Matching criteria
                "app_ids": rule.raw.get("app_ids") or None,
                "app_category_ids": rule.raw.get("app_category_ids") or None,
                "network_ids": rule.raw.get("network_ids") or None,
                "domains": rule.raw.get("domains") or None,
                "target_client_macs": target_client_macs or None,
            }
        )
    logger.debug("Fetched %d UniFi traffic rules", len(traffic_rules))
    return traffic_rules


@timeit
def load_traffic_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi traffic rules into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of traffic rule data
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi traffic rules to the graph.", len(data))
    load(
        neo4j_session,
        UnifiTrafficRuleSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
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
    logger.debug("Running UniFi traffic rule cleanup job")
    GraphJob.from_node_schema(UnifiTrafficRuleSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi traffic rules.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    traffic_rules = await get(controller)
    load_traffic_rules(
        neo4j_session, traffic_rules, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
