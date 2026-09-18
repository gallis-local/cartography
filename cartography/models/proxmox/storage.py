"""
Data models for Proxmox storage resources.

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import BLOCK_STORAGE
from cartography.models.ontology.labels import FILE_STORAGE

# ProxmoxStorage Node Schema


@dataclass(frozen=True)
class ProxmoxStorageNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxStorage node.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this storage, in the form `{cluster_id}/storage/{name}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Storage id as configured in the cluster's storage configuration.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Storage backend type, e.g. `dir`, `lvm`, `lvmthin`, `zfspool`, `nfs`, `cifs`, `rbd`, `cephfs` or `pbs`.",
    )
    content_types: PropertyRef = PropertyRef(
        "content_types",
        description="Content kinds the storage accepts, split from the API's comma-separated `content` field, e.g. `images`, `rootdir`, `vztmpl`, `backup`, `iso` or `snippets`.",
    )
    shared: PropertyRef = PropertyRef(
        "shared",
        description="True when every node sees the same data on this storage, so guests can migrate without copying their disks.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="True when the storage is active, derived from the API's `disable` flag.",
    )
    total: PropertyRef = PropertyRef(
        "total",
        description="Capacity of the storage in bytes, taken as the largest value any node reported for it. 0 when no node reported status.",
    )
    used: PropertyRef = PropertyRef(
        "used",
        description="Space used on the storage in bytes, taken as the largest value any node reported for it. 0 when no node reported status.",
    )
    available: PropertyRef = PropertyRef(
        "available",
        description="Free space on the storage in bytes, taken as the largest value any node reported for it. 0 when no node reported status.",
    )


@dataclass(frozen=True)
class ProxmoxStorageToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxStorageToClusterRel(CartographyRelSchema):
    """
    Storage belongs to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxStorageToClusterRelProperties = (
        ProxmoxStorageToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxStorageSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxStorage.

    Storage resources belong to clusters and are available on nodes.
    """

    label: str = "ProxmoxStorage"
    properties: ProxmoxStorageNodeProperties = ProxmoxStorageNodeProperties()
    sub_resource_relationship: ProxmoxStorageToClusterRel = ProxmoxStorageToClusterRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            # Block storage types
            BLOCK_STORAGE.when(type="lvm"),
            BLOCK_STORAGE.when(type="lvmthin"),
            BLOCK_STORAGE.when(type="rbd"),
            BLOCK_STORAGE.when(type="iscsi"),
            BLOCK_STORAGE.when(type="zfs"),
            # File storage types
            FILE_STORAGE.when(type="dir"),
            FILE_STORAGE.when(type="zfspool"),
            FILE_STORAGE.when(type="cephfs"),
            FILE_STORAGE.when(type="nfs"),
            FILE_STORAGE.when(type="cifs"),
            FILE_STORAGE.when(type="glusterfs"),
        ]
    )


# MatchLink Schema for Storage Availability Relationships


@dataclass(frozen=True)
class ProxmoxStorageToNodeMatchLinkProperties(CartographyRelProperties):
    """
    Properties for storage to node AVAILABLE_ON relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxStorageToNodeMatchLink(CartographyRelSchema):
    """
    Connects storage to the nodes where it's available.
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("node_id"),  # Node ID
        }
    )
    source_node_label: str = "ProxmoxStorage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("storage_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AVAILABLE_ON"
    properties: ProxmoxStorageToNodeMatchLinkProperties = (
        ProxmoxStorageToNodeMatchLinkProperties()
    )
