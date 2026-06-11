"""
Data models for Proxmox storage resources.

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher

# ProxmoxStorage Node Schema


@dataclass(frozen=True)
class ProxmoxStorageNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxStorage node.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    type: PropertyRef = PropertyRef("type")
    content_types: PropertyRef = PropertyRef("content_types")
    shared: PropertyRef = PropertyRef("shared")
    enabled: PropertyRef = PropertyRef("enabled")
    total: PropertyRef = PropertyRef("total")
    used: PropertyRef = PropertyRef("used")
    available: PropertyRef = PropertyRef("available")


@dataclass(frozen=True)
class ProxmoxStorageToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxStorageToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxStorage)

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
            ConditionalNodeLabel(label="BlockStorage", conditions={"type": "lvm"}),
            ConditionalNodeLabel(label="BlockStorage", conditions={"type": "lvmthin"}),
            ConditionalNodeLabel(label="BlockStorage", conditions={"type": "rbd"}),
            ConditionalNodeLabel(label="BlockStorage", conditions={"type": "iscsi"}),
            ConditionalNodeLabel(label="BlockStorage", conditions={"type": "zfs"}),
            # File storage types
            ConditionalNodeLabel(label="FileStorage", conditions={"type": "dir"}),
            ConditionalNodeLabel(label="FileStorage", conditions={"type": "zfspool"}),
            ConditionalNodeLabel(label="FileStorage", conditions={"type": "cephfs"}),
            ConditionalNodeLabel(label="FileStorage", conditions={"type": "nfs"}),
            ConditionalNodeLabel(label="FileStorage", conditions={"type": "cifs"}),
            ConditionalNodeLabel(label="FileStorage", conditions={"type": "glusterfs"}),
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
    MatchLink: (:ProxmoxStorage)-[:AVAILABLE_ON]->(:ProxmoxNode)

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
