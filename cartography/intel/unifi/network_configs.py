import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.network_config import UnifiNetworkConfigSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi object-oriented network configurations from the controller.

    :param controller: Controller instance
    :return: List of network config data
    """
    logger.debug("Fetching UniFi network configurations")
    await controller.object_oriented_network_configs.update()

    # Convert aiounifi ObjectOrientedNetworkConfig objects to dictionaries
    configs = []
    for config in controller.object_oriented_network_configs.values():
        # Extract secure configuration
        secure = config.secure or {}
        # Extract QoS configuration
        qos = config.qos or {}
        # Extract route configuration
        route = config.route or {}

        configs.append(
            {
                "id": config.id,
                "name": config.name,
                "enabled": config.enabled,
                "target_type": config.target_type,
                "targets": config.targets or [],
                # Secure configuration
                "secure_enabled": secure.get("enabled", False),
                "secure_firewall_rules": secure.get("firewall_rules"),
                "secure_group_ids": secure.get("group_ids") or [],
                # QoS configuration
                "qos_enabled": qos.get("enabled", False),
                "qos_bandwidth_limit": qos.get("bandwidth_limit"),
                "qos_dscp": qos.get("dscp"),
                # Route configuration
                "route_enabled": route.get("enabled", False),
                "route_nexthop": route.get("nexthop"),
                "route_network": route.get("network"),
            }
        )
    logger.debug("Fetched %d UniFi network configurations", len(configs))
    return configs


@timeit
def load_network_configs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi network configurations into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of network config data
    :param site_id: Site ID for the configs
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi network configurations to the graph.", len(data))
    load(
        neo4j_session,
        UnifiNetworkConfigSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi network configurations from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi network config cleanup job")
    GraphJob.from_node_schema(UnifiNetworkConfigSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi network configurations.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    configs = await get(controller)
    load_network_configs(
        neo4j_session, configs, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
