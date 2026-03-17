"""
Sync Proxmox resource pools.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.proxmox.pool import ProxmoxPoolSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


@timeit
def get_pools(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all resource pools in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of pool dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.pools.get()


@timeit
def get_pool_details(proxmox_client: Any, poolid: str) -> dict[str, Any]:
    """
    Get detailed information about a specific pool.

    :param proxmox_client: Proxmox API client
    :param poolid: Pool ID
    :return: Pool details dict
    :raises: Exception if API call fails
    """
    return proxmox_client.pools(poolid).get()


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# ============================================================================


def transform_pool_data(
    pools: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform pool data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param pools: Raw pool data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed pool dicts
    """
    transformed_pools = []

    for pool in pools:
        # Required field - use direct access
        poolid = pool["poolid"]

        # NEW UID PATTERN: Consistent path-like structure
        # OLD: f"{cluster_id}:{poolid}"
        # NEW: f"{cluster_id}/pool/{poolid}"
        transformed_pools.append(
            {
                "id": f"{cluster_id}/pool/{poolid}",
                "poolid": poolid,
                "comment": pool.get("comment"),
                "cluster_id": cluster_id,
            }
        )

    return transformed_pools


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# ============================================================================


def load_pools(
    neo4j_session: neo4j.Session,
    pools: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load pool data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param pools: List of transformed pool dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxPoolSchema(),
        pools,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_pool_member_relationships(
    neo4j_session: neo4j.Session,
    pool_members: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Create relationships between pools and their member resources (VMs, storage).

    Pool members can include VMs/containers and storage resources.
    Uses MatchLinks to connect pools to VMs and storage.

    :param neo4j_session: Neo4j session
    :param pool_members: List of pool-member mappings
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import load_matchlinks
    from cartography.models.proxmox.pool import ProxmoxPoolToStorageMatchLink
    from cartography.models.proxmox.pool import ProxmoxPoolToVMMatchLink

    if not pool_members:
        return

    # Separate VM/container members from storage members
    vm_members = [m for m in pool_members if m["type"] in ("qemu", "lxc")]
    storage_members = [m for m in pool_members if m["type"] == "storage"]

    # Create relationships to VMs/containers
    if vm_members:
        load_matchlinks(
            neo4j_session,
            ProxmoxPoolToVMMatchLink(),
            vm_members,
            lastupdated=update_tag,
            _sub_resource_label="ProxmoxCluster",
            _sub_resource_id=cluster_id,
        )

    # Create relationships to storage
    if storage_members:
        load_matchlinks(
            neo4j_session,
            ProxmoxPoolToStorageMatchLink(),
            storage_members,
            lastupdated=update_tag,
            _sub_resource_label="ProxmoxCluster",
            _sub_resource_id=cluster_id,
        )


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# ============================================================================


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync pool data.

    Follows Cartography's Get → Transform → Load pattern.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox resource pools")

    # GET - retrieve data from API
    pools = get_pools(proxmox_client)

    # Collect pool member information
    pool_members = []
    for pool in pools:
        poolid = pool["poolid"]
        details = get_pool_details(proxmox_client, poolid)

        # Extract members from pool details
        if "members" in details:
            for member in details["members"]:
                member_data = {
                    "pool_id": poolid,  # Pool ID (bare poolid, used by MatchLink to find pool)
                    "type": member.get("type"),
                }

                if member.get("type") in ("qemu", "lxc"):
                    # For VMs/containers, use integer VMID (MatchLink matches on vmid property)
                    member_data["vmid"] = member.get("vmid")
                elif member.get("type") == "storage":
                    # For storage, build full storage ID using new pattern
                    # MatchLink will match on the full storage ID
                    storage_name = member.get("storage")
                    member_data["storage_id"] = f"{cluster_id}/storage/{storage_name}"

                pool_members.append(member_data)

    # TRANSFORM - manipulate data for ingestion
    transformed_pools = transform_pool_data(pools, cluster_id)

    # LOAD - ingest to Neo4j
    load_pools(neo4j_session, transformed_pools, cluster_id, update_tag)
    load_pool_member_relationships(neo4j_session, pool_members, cluster_id, update_tag)

    # CLEANUP - remove stale pools
    cleanup(neo4j_session, common_job_parameters)

    logger.info(
        f"Synced {len(transformed_pools)} resource pools with {len(pool_members)} members"
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    """
    Remove stale pool data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    """
    GraphJob.from_node_schema(ProxmoxPoolSchema(), common_job_parameters).run(
        neo4j_session
    )
