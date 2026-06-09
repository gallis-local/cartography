"""
Proxmox firewall global options sync module.

Syncs firewall configuration options at cluster and node levels.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.proxmox.firewalloptions import ProxmoxFirewallOptionsSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cluster_firewall_options(proxmox_client: Any) -> dict[str, Any]:
    """
    Get cluster-level firewall options.

    :param proxmox_client: Proxmox API client
    :return: Dict of firewall options
    """
    try:
        return proxmox_client.cluster.firewall.options.get()
    except Exception as e:
        logger.debug(f"Could not fetch cluster firewall options: {e}")
        return {}

@timeit
def get_node_firewall_options(proxmox_client: Any, node_name: str) -> dict[str, Any]:
    """
    Get node-level firewall options.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: Dict of firewall options
    """
    try:
        return proxmox_client.nodes(node_name).firewall.options.get()
    except Exception as e:
        logger.debug(f"Could not fetch firewall options for node {node_name}: {e}")
        return {}


def transform_firewall_options_data(
    options: dict[str, Any],
    cluster_id: str,
    scope: str,
    scope_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Transform firewall options data into standard format.

    :param options: Raw firewall options data from API
    :param cluster_id: Parent cluster ID
    :param scope: Options scope (cluster or node)
    :param scope_id: Scope identifier (node name for node-level)
    :return: Transformed firewall options dict or None if empty
    """
    if not options:
        return None
    if scope == "cluster":
        options_id = f"{cluster_id}/firewall/options"
    elif scope == "node":
        options_id = f"{cluster_id}/node/{scope_id}/firewall/options"
    elif scope == "vm":
        options_id = f"{cluster_id}/vm/{scope_id}/firewall/options"
    else:
        # Fallback for unknown scopes
        options_id = f"{cluster_id}/firewall/{scope}/{scope_id}/options" if scope_id else f"{cluster_id}/firewall/{scope}/options"

    return {
        "id": options_id,
        "cluster_id": cluster_id,
        "scope": scope,
        "scope_id": scope_id,
        "node_id": f"{cluster_id}/node/{scope_id}" if scope == "node" and scope_id else None,
        "enable": options.get("enable", 0) == 1,  # Convert to boolean
        "policy_in": options.get("policy_in"),  # ACCEPT, REJECT, DROP
        "policy_out": options.get("policy_out"),
        "log_level_in": options.get("log_level_in"),
        "log_level_out": options.get("log_level_out"),
        "nf_conntrack_max": options.get("nf_conntrack_max"),
        "nf_conntrack_tcp_timeout_established": options.get(
            "nf_conntrack_tcp_timeout_established"
        ),
    }


def load_firewall_options(
    neo4j_session: neo4j.Session,
    options_list: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load firewall options data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param options_list: List of transformed firewall options dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not options_list:
        return

    load(
        neo4j_session,
        ProxmoxFirewallOptionsSchema(),
        options_list,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync firewall global options.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Proxmox cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters for GraphJob
    """
    logger.info("Syncing Proxmox firewall global options")

    all_options = []

    cluster_options = get_cluster_firewall_options(proxmox_client)
    transformed_cluster_options = transform_firewall_options_data(
        cluster_options, cluster_id, "cluster"
    )
    if transformed_cluster_options:
        all_options.append(transformed_cluster_options)

    nodes = proxmox_client.nodes.get()
    for node in nodes:
        node_name = node["node"]
        node_options = get_node_firewall_options(proxmox_client, node_name)
        transformed_node_options = transform_firewall_options_data(
            node_options, cluster_id, "node", node_name
        )
        if transformed_node_options:
            all_options.append(transformed_node_options)

    load_firewall_options(neo4j_session, all_options, cluster_id, update_tag)

    logger.info(f"Synced {len(all_options)} firewall options configurations")

    cleanup(neo4j_session, common_job_parameters)

def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    """
    Remove stale firewall options data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    """
    GraphJob.from_node_schema(ProxmoxFirewallOptionsSchema(), common_job_parameters).run(
        neo4j_session
    )
