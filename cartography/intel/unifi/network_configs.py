import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller
from aiounifi.errors import AiounifiException
from aiounifi.errors import LoginRequired
from aiounifi.errors import NoPermission
from aiounifi.models.api import ApiRequest

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.network_config import UnifiNetworkConfigSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi network (VLAN) configurations from the controller.

    aiounifi has no dedicated handler for this resource, so this hits the raw
    `/rest/networkconf` endpoint directly (the same source that populates each
    device's `network_table`), following the same raw-ApiRequest pattern used
    by admins.py for `/rest/admin`.

    :param controller: Controller instance
    :return: List of network config data
    """
    logger.debug("Fetching UniFi network configurations")
    try:
        response = await controller.request(
            ApiRequest(method="get", path="/rest/networkconf")
        )
    except NoPermission:
        logger.warning(
            "UniFi network config listing requires elevated privileges. "
            "Grant the service account access to network settings to enable this.",
        )
        return []
    except LoginRequired:
        logger.warning(
            "UniFi network config listing failed: session expired or credentials "
            "rejected (LoginRequired). Check that the service account credentials "
            "are valid.",
        )
        return []
    except AiounifiException as exc:
        logger.warning(
            "UniFi network config listing failed with unexpected API error "
            "(%s: %s). Skipping network config sync.",
            type(exc).__name__,
            exc,
        )
        return []

    configs = []
    for raw in response.get("data", []):
        configs.append(
            {
                "id": raw.get("_id"),
                "name": raw.get("name"),
                "enabled": raw.get("enabled", True),
                "purpose": raw.get("purpose"),
                "networkgroup": raw.get("networkgroup"),
                "domain_name": raw.get("domain_name"),
                "vlan_enabled": raw.get("vlan_enabled", False),
                "vlan": raw.get("vlan"),
                "ip_subnet": raw.get("ip_subnet"),
                "is_guest": raw.get("is_guest", False),
                "is_nat": raw.get("is_nat", False),
                "attr_no_delete": raw.get("attr_no_delete", False),
                "dhcpd_enabled": raw.get("dhcpd_enabled", False),
                "dhcpd_start": raw.get("dhcpd_start"),
                "dhcpd_stop": raw.get("dhcpd_stop"),
                "dhcpd_leasetime": raw.get("dhcpd_leasetime"),
                "dhcpd_dns_enabled": raw.get("dhcpd_dns_enabled", False),
                "dhcpd_dns_1": raw.get("dhcpd_dns_1"),
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
