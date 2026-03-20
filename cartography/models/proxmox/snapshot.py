"""
Data models for Proxmox VM/container snapshots.

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher

# ============================================================================
# ProxmoxSnapshot Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxSnapshotNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSnapshot node.

    Represents VM/container snapshots in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    vmid: PropertyRef = PropertyRef("vmid", extra_index=True)
    vm_type: PropertyRef = PropertyRef("vm_type")  # qemu or lxc
    node: PropertyRef = PropertyRef("node")
    description: PropertyRef = PropertyRef("description")
    snaptime: PropertyRef = PropertyRef("snaptime")  # Unix timestamp
    vmstate: PropertyRef = PropertyRef("vmstate")  # Whether VM state is included (QEMU only)
    parent: PropertyRef = PropertyRef("parent")  # Parent snapshot name


@dataclass(frozen=True)
class ProxmoxSnapshotToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSnapshot to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSnapshotToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSnapshot)

    Snapshots belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSnapshotToClusterRelProperties = ProxmoxSnapshotToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxSnapshotToVMRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSnapshot to ProxmoxVM.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSnapshotToVMRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxSnapshot)-[:SNAPSHOT_OF]->(:ProxmoxVM)

    Snapshots are snapshots of VMs/containers.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid"),
            "cluster_id": PropertyRef("cluster_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SNAPSHOT_OF"
    properties: ProxmoxSnapshotToVMRelProperties = ProxmoxSnapshotToVMRelProperties()


@dataclass(frozen=True)
class ProxmoxSnapshotSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxSnapshot.

    VM/container snapshots for backup and recovery.
    """

    label: str = "ProxmoxSnapshot"
    properties: ProxmoxSnapshotNodeProperties = ProxmoxSnapshotNodeProperties()
    sub_resource_relationship: ProxmoxSnapshotToClusterRel = ProxmoxSnapshotToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxSnapshotToVMRel(),
        ]
    )
