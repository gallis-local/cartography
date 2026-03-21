"""
Sync Proxmox storage resources.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.proxmox.storage import ProxmoxStorageSchema
from cartography.models.proxmox.storage import ProxmoxStorageToNodeMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_storage(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all storage definitions from Proxmox.

    :param proxmox_client: Proxmox API client
    :return: List of storage dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.storage.get()

@timeit
def get_storage_status(proxmox_client: Any, node_name: str) -> list[dict[str, Any]]:
    """
    Get storage status for a specific node.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of storage status dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes(node_name).storage.get()


def transform_storage_data(
    storage_list: list[dict[str, Any]],
    storage_status_map: dict[str, list[dict[str, Any]]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform storage data into standard format.

    :param storage_list: Raw storage definitions from API
    :param storage_status_map: Map of node_name -> storage status list
    :param cluster_id: Parent cluster ID
    :return: List of transformed storage dicts
    """
    transformed_storage = []

    for storage in storage_list:
        # Required fields
        storage_id = storage["storage"]

        # Parse content types
        content_types = []
        if storage.get("content"):
            content_types = [c.strip() for c in storage["content"].split(",")]

        # Determine which nodes have access to this storage
        nodes = []
        if storage.get("nodes"):
            # Specific nodes listed
            nodes = [n.strip() for n in storage["nodes"].split(",")]
        else:
            # All nodes have access
            nodes = list(storage_status_map.keys())

        # Try to get size information from status
        total = 0
        used = 0
        available = 0

        for node_name, status_list in storage_status_map.items():
            for status in status_list:
                if status.get("storage") == storage_id:
                    total = max(total, status.get("total", 0))
                    used = max(used, status.get("used", 0))
                    available = max(available, status.get("avail", 0))
                    break
        transformed_storage.append(
            {
                "id": f"{cluster_id}/storage/{storage_id}",
                "name": storage_id,
                "cluster_id": cluster_id,
                "type": storage.get("type"),
                "content_types": content_types,
                "shared": storage.get("shared", 0) == 1,
                "enabled": storage.get("disable", 0) == 0,
                "total": total,
                "used": used,
                "available": available,
                "nodes": nodes,
            }
        )

    return transformed_storage


def load_storage(
    neo4j_session: neo4j.Session,
    storage_list: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load storage data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param storage_list: List of transformed storage dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxStorageSchema(),
        storage_list,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )

def load_storage_node_relationships(
    neo4j_session: neo4j.Session,
    storage_list: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Create relationships between storage and nodes.

    This creates many-to-many relationships between storage and nodes.
    Uses MatchLinks to connect storage to nodes where it's available.

    :param neo4j_session: Neo4j session
    :param storage_list: List of transformed storage dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    # Flatten storage -> nodes into individual relationships
    relationships = []
    for storage in storage_list:
        for node_name in storage["nodes"]:
            # Build full node ID using cluster_id already present in the dict
            node_id = f"{storage['cluster_id']}/node/{node_name}"

            relationships.append(
                {
                    "storage_id": storage["id"],
                    "node_id": node_id,
                }
            )

    if not relationships:
        return

    load_matchlinks(
        neo4j_session,
        ProxmoxStorageToNodeMatchLink(),
        relationships,
        lastupdated=update_tag,
        _sub_resource_label="ProxmoxCluster",
        _sub_resource_id=cluster_id,
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
    Sync storage resources.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox storage")

    storage_list = get_storage(proxmox_client)

    # Get storage status from each node for size information
    nodes = proxmox_client.nodes.get()
    storage_status_map = {}

    for node in nodes:
        node_name = node["node"]
        storage_status = get_storage_status(proxmox_client, node_name)
        storage_status_map[node_name] = storage_status

    transformed_storage = transform_storage_data(
        storage_list, storage_status_map, cluster_id
    )

    load_storage(neo4j_session, transformed_storage, cluster_id, update_tag)
    load_storage_node_relationships(
        neo4j_session, transformed_storage, cluster_id, update_tag
    )

    logger.info(f"Synced {len(transformed_storage)} storage resources")

    cleanup(neo4j_session, common_job_parameters, cluster_id, update_tag)

def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Remove stale storage data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    :param cluster_id: Cluster ID for MatchLink cleanup scoping
    :param update_tag: Sync timestamp for MatchLink cleanup
    """
    GraphJob.from_node_schema(ProxmoxStorageSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_matchlink(
        ProxmoxStorageToNodeMatchLink(), "ProxmoxCluster", cluster_id, update_tag
    ).run(neo4j_session)
