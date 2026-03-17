"""
Proxmox snapshot sync module.

Syncs VM and container snapshots.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.graph.job import GraphJob
from cartography.models.proxmox.snapshot import ProxmoxSnapshotSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


def get_snapshots_for_vm(
    proxmox_client: Any,
    node_name: str,
    vmid: int,
    vm_type: str,
) -> List[Dict[str, Any]]:
    """
    Get snapshots for a specific VM or container.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :param vmid: VM ID
    :param vm_type: VM type (qemu or lxc)
    :return: List of snapshot dicts
    """
    try:
        if vm_type == "qemu":
            response = proxmox_client.nodes(node_name).qemu(vmid).snapshot.get()
        elif vm_type == "lxc":
            response = proxmox_client.nodes(node_name).lxc(vmid).snapshot.get()
        else:
            logger.warning(f"Unknown VM type {vm_type} for vmid {vmid}")
            return []

        # Filter out the 'current' pseudo-snapshot
        snapshots = [s for s in response if s.get("name") != "current"]
        return snapshots

    except Exception as e:
        logger.debug(
            f"Could not fetch snapshots for {vm_type} {vmid} on node {node_name}: {e}"
        )
        return []


def get_all_snapshots(
    proxmox_client: Any,
    vms: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Get all snapshots across all VMs and containers.

    :param proxmox_client: Proxmox API client
    :param vms: List of VM/container dicts (must have 'node', 'vmid', 'type' fields)
    :return: List of snapshot dicts with node and VM metadata
    """
    all_snapshots = []

    for vm in vms:
        node_name = vm.get("node")
        vmid = vm.get("vmid")
        vm_type = vm.get("type")

        if not node_name or not vmid or not vm_type:
            logger.warning(f"Skipping VM with missing fields: {vm}")
            continue

        snapshots = get_snapshots_for_vm(proxmox_client, node_name, vmid, vm_type)

        # Add VM metadata to each snapshot
        for snapshot in snapshots:
            snapshot["node"] = node_name
            snapshot["vmid"] = vmid
            snapshot["vm_type"] = vm_type

        all_snapshots.extend(snapshots)

    return all_snapshots


# ============================================================================
# TRANSFORM functions
# ============================================================================


def transform_snapshot_data(
    snapshots: List[Dict[str, Any]],
    cluster_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform snapshot data into standard format.

    :param snapshots: Raw snapshot data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed snapshot dicts
    """
    transformed_snapshots = []

    for snapshot in snapshots:
        # Required fields
        name = snapshot["name"]
        vmid = snapshot["vmid"]
        node = snapshot["node"]
        vm_type = snapshot["vm_type"]

        # NEW UID PATTERN: Node-agnostic, hierarchical structure
        # OLD: f"{cluster_id}:{node}/{vm_type}/{vmid}:{name}"  # Included node (mutable)
        # NEW: f"{cluster_id}/vm/{vmid}/snapshot/{name}"  # Node-agnostic, clear hierarchy
        snapshot_id = f"{cluster_id}/vm/{vmid}/snapshot/{name}"

        transformed_snapshots.append(
            {
                "id": snapshot_id,
                "name": name,
                "cluster_id": cluster_id,
                "vmid": vmid,
                "vm_type": vm_type,
                "node": node,  # Still store node, but not in UID (mutable state)
                "description": snapshot.get("description"),
                "snaptime": snapshot.get("snaptime"),
                "vmstate": snapshot.get("vmstate", 0) == 1,  # Convert to boolean
                "parent": snapshot.get("parent"),
            }
        )

    return transformed_snapshots


# ============================================================================
# LOAD functions
# ============================================================================


def load_snapshots(
    neo4j_session: neo4j.Session,
    snapshots: List[Dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load snapshot data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param snapshots: List of transformed snapshot dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import load

    load(
        neo4j_session,
        ProxmoxSnapshotSchema(),
        snapshots,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


# ============================================================================
# SYNC function
# ============================================================================


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
    vms: List[Dict[str, Any]],
) -> None:
    """
    Sync VM and container snapshots.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Proxmox cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters for GraphJob
    :param vms: List of VMs/containers to fetch snapshots for
    """
    logger.info("Syncing Proxmox snapshots")

    # GET - retrieve data from API
    raw_snapshots = get_all_snapshots(proxmox_client, vms)

    # TRANSFORM - convert to standard format
    transformed_snapshots = transform_snapshot_data(raw_snapshots, cluster_id)

    # LOAD - ingest to Neo4j
    load_snapshots(neo4j_session, transformed_snapshots, cluster_id, update_tag)

    logger.info(f"Synced {len(transformed_snapshots)} snapshots")


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Remove stale snapshot data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    """
    GraphJob.from_node_schema(ProxmoxSnapshotSchema(), common_job_parameters).run(
        neo4j_session
    )
