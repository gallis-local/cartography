"""
Sync Proxmox High Availability (HA) resources.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.proxmox.ha import ProxmoxHAGroupSchema
from cartography.models.proxmox.ha import ProxmoxHAResourceSchema
from cartography.models.proxmox.ha import ProxmoxHAResourceToVMMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


@timeit
def get_ha_groups(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all HA groups in the cluster.

    Note: HA groups are deprecated in newer Proxmox versions and have been
    migrated to HA rules. Returns empty list if groups API is unavailable.

    :param proxmox_client: Proxmox API client
    :return: List of HA group dicts (empty if unavailable)
    """
    from proxmoxer.core import ResourceException

    try:
        return proxmox_client.cluster.ha.groups.get()
    except ResourceException as e:
        # HA groups deprecated/migrated to rules in newer Proxmox versions
        if "migrated to rules" in str(e).lower() or "cannot index groups" in str(e).lower():
            logger.info("HA groups API unavailable (deprecated/migrated to rules) - skipping HA group sync")
            return []
        raise


@timeit
def get_ha_resources(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all HA resources in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of HA resource dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.ha.resources.get()


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# ============================================================================


def transform_ha_group_data(
    groups: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform HA group data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param groups: Raw HA group data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed HA group dicts
    """
    transformed_groups = []

    for group in groups:
        # Required field - use direct access
        group_name = group["group"]

        # NEW UID PATTERN: Consistent path-like structure
        # OLD: f"{cluster_id}:{group_name}"
        # NEW: f"{cluster_id}/ha/group/{group_name}"
        transformed_groups.append(
            {
                "id": f"{cluster_id}/ha/group/{group_name}",
                "group": group_name,
                "cluster_id": cluster_id,
                "nodes": group.get("nodes"),
                "restricted": group.get("restricted", False),
                "nofailback": group.get("nofailback", False),
                "comment": group.get("comment"),
            }
        )

    return transformed_groups


def transform_ha_resource_data(
    resources: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform HA resource data into standard format.

    :param resources: Raw HA resource data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed HA resource dicts
    """
    transformed_resources = []

    for resource in resources:
        # Required field - service ID (format: vm:100, ct:200)
        sid = resource["sid"]

        # NEW UID PATTERN: Consistent path-like structure
        # OLD: f"{cluster_id}:{sid}"
        # NEW: f"{cluster_id}/ha/resource/{sid}"
        transformed_resources.append(
            {
                "id": f"{cluster_id}/ha/resource/{sid}",
                "sid": sid,
                "cluster_id": cluster_id,
                "state": resource.get("state"),
                "group": resource.get("group"),
                "max_restart": resource.get("max_restart"),
                "max_relocate": resource.get("max_relocate"),
                "comment": resource.get("comment"),
            }
        )

    return transformed_resources


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# ============================================================================


def load_ha_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load HA group data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param groups: List of transformed HA group dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxHAGroupSchema(),
        groups,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_ha_resources(
    neo4j_session: neo4j.Session,
    resources: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load HA resource data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param resources: List of transformed HA resource dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxHAResourceSchema(),
        resources,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_ha_resource_vm_relationships(
    neo4j_session: neo4j.Session,
    resources: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Create relationships between HA resources and their VMs.

    Uses MatchLinks to connect HA resources to VMs they protect.

    :param neo4j_session: Neo4j session
    :param resources: List of HA resource dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import load_matchlinks
    from cartography.models.proxmox.ha import ProxmoxHAResourceToVMMatchLink

    # Extract VM IDs from service IDs (format: vm:100, ct:200)
    vm_mappings = []
    for resource in resources:
        sid = resource["sid"]
        if ":" in sid:
            parts = sid.split(":", 1)
            if parts[0] in ("vm", "ct") and parts[1].isdigit():
                vm_mappings.append(
                    {
                        "sid": sid,
                        "ha_resource_id": f"{cluster_id}/ha/resource/{sid}",  # Full cluster-scoped ID for MatchLink source matching
                        "vmid": int(parts[1]),
                        "cluster_id": cluster_id,
                    }
                )

    if not vm_mappings:
        return

    load_matchlinks(
        neo4j_session,
        ProxmoxHAResourceToVMMatchLink(),
        vm_mappings,
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
    Sync HA groups and resources.

    Follows Cartography's Get → Transform → Load pattern.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox HA groups and resources")

    # GET - retrieve data from API
    groups = get_ha_groups(proxmox_client)
    resources = get_ha_resources(proxmox_client)

    # TRANSFORM - manipulate data for ingestion
    transformed_groups = transform_ha_group_data(groups, cluster_id)
    transformed_resources = transform_ha_resource_data(resources, cluster_id)

    # LOAD - ingest to Neo4j
    if transformed_groups:
        load_ha_groups(neo4j_session, transformed_groups, cluster_id, update_tag)

    if transformed_resources:
        load_ha_resources(neo4j_session, transformed_resources, cluster_id, update_tag)
        load_ha_resource_vm_relationships(
            neo4j_session, transformed_resources, cluster_id, update_tag
        )

    logger.info(
        f"Synced {len(transformed_groups)} HA groups and {len(transformed_resources)} HA resources"
    )

    cleanup(neo4j_session, common_job_parameters, cluster_id, update_tag)


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Remove stale HA data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    :param cluster_id: Cluster ID for MatchLink cleanup scoping
    :param update_tag: Sync timestamp for MatchLink cleanup
    """
    GraphJob.from_node_schema(ProxmoxHAGroupSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(ProxmoxHAResourceSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_matchlink(
        ProxmoxHAResourceToVMMatchLink(), "ProxmoxCluster", cluster_id, update_tag
    ).run(neo4j_session)
