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

# ProxmoxSnapshot Node Schema


@dataclass(frozen=True)
class ProxmoxSnapshotNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSnapshot node.

    Represents VM/container snapshots in Proxmox VE.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this snapshot, in the form `{cluster_id}/vm/{vmid}/snapshot/{name}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Snapshot name. The `current` pseudo-snapshot that Proxmox returns for the live state is filtered out and never ingested.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    vmid: PropertyRef = PropertyRef(
        "vmid",
        extra_index=True,
        description="Numeric id of the guest this snapshot was taken from.",
    )
    vm_type: PropertyRef = PropertyRef(
        "vm_type",
        description="Technology of the snapshotted guest: `qemu` for a virtual machine, `lxc` for a container.",
    )
    node: PropertyRef = PropertyRef(
        "node",
        description="Name of the node the guest was on when the snapshot was collected. Guests move between nodes, so this is not part of the id.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Free-text description recorded when the snapshot was taken.",
    )
    snaptime: PropertyRef = PropertyRef(
        "snaptime",
        description="When the snapshot was taken, as a Unix epoch timestamp in seconds.",
    )
    vmstate: PropertyRef = PropertyRef(
        "vmstate",
        description="True when the snapshot also captured the guest's RAM, so it can be resumed in place rather than only rolled back to its disk state.",
    )
    parent: PropertyRef = PropertyRef(
        "parent",
        description="Name of the snapshot this one was taken from. Proxmox reports an empty string on the root of the chain.",
    )


@dataclass(frozen=True)
class ProxmoxSnapshotToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSnapshotToClusterRel(CartographyRelSchema):
    """
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
    properties: ProxmoxSnapshotToClusterRelProperties = (
        ProxmoxSnapshotToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxSnapshotToVMRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSnapshotToVMRel(CartographyRelSchema):
    """
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
class ProxmoxSnapshotToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSnapshotToParentRel(CartographyRelSchema):
    """
    Snapshots form a chain: each snapshot (other than the root) has a parent
    snapshot it was taken from. Proxmox exposes this via the `parent` field
    on GET /nodes/{node}/qemu|lxc/{vmid}/snapshot (see
    https://pve.proxmox.com/pve-docs/api-viewer/). Modeling this lets callers
    walk the snapshot lineage of a VM/container.
    """

    target_node_label: str = "ProxmoxSnapshot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("parent_snapshot_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CHILD_OF"
    properties: ProxmoxSnapshotToParentRelProperties = (
        ProxmoxSnapshotToParentRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxSnapshotSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxSnapshot.

    VM/container snapshots for backup and recovery.
    """

    label: str = "ProxmoxSnapshot"
    properties: ProxmoxSnapshotNodeProperties = ProxmoxSnapshotNodeProperties()
    sub_resource_relationship: ProxmoxSnapshotToClusterRel = (
        ProxmoxSnapshotToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxSnapshotToVMRel(),
            ProxmoxSnapshotToParentRel(),
        ]
    )
