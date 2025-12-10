import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.firewall_policy import UnifiFirewallPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller, site_id: str) -> list[dict[str, Any]]:
    """
    Retrieve UniFi firewall policies from the controller.

    :param controller: Controller instance
    :param site_id: Site ID for the firewall policies
    :return: List of firewall policy data
    """
    logger.info("Fetching UniFi firewall policies")
    await controller.firewall_policies.update()

    # Convert aiounifi FirewallPolicy objects to dictionaries
    firewall_policies = []
    for policy in controller.firewall_policies.values():
        firewall_policies.append(
            {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "enabled": policy.enabled,
                "action": policy.action,
                "protocol": policy.protocol,
                "predefined": policy.predefined,
                "index": policy.index,
                "connection_state_type": policy.connection_state_type,
                "logging": policy.raw.get("logging", False),
                "site_id": site_id,
            }
        )
    return firewall_policies


@timeit
def load_firewall_policies(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load UniFi firewall policies into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of firewall policy data
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi firewall policies into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiFirewallPolicySchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi firewall policies from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiFirewallPolicySchema(), common_job_parameters).run(
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
    Sync UniFi firewall policies.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param site_id: Site ID for the firewall policies
    :param common_job_parameters: Common job parameters
    :return: List of firewall policy data
    """
    firewall_policies = await get(controller, site_id)
    load_firewall_policies(neo4j_session, firewall_policies, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return firewall_policies
