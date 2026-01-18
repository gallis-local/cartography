"""
Data models for Proxmox resource pools.

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher

# ============================================================================
# ProxmoxPool Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxPoolNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxPool node.

    Resource pools are used to organize VMs, containers, and storage.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    poolid: PropertyRef = PropertyRef("poolid", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    cluster_id: PropertyRef = PropertyRef("cluster_id")


@dataclass(frozen=True)
class ProxmoxPoolToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxPool to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxPoolToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxPool)-[:RESOURCE]->(:ProxmoxCluster)

    Pools belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxPoolToClusterRelProperties = ProxmoxPoolToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxPoolSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxPool.

    Pools organize VMs, containers, and storage resources.
    """

    label: str = "ProxmoxPool"
    properties: ProxmoxPoolNodeProperties = ProxmoxPoolNodeProperties()
    sub_resource_relationship: ProxmoxPoolToClusterRel = ProxmoxPoolToClusterRel()


# ============================================================================
# MatchLink Schemas for Pool Containment Relationships
# ============================================================================


@dataclass(frozen=True)
class ProxmoxPoolToVMMatchLinkProperties(CartographyRelProperties):
    """
    Properties for pool to VM CONTAINS_VM relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxPoolToVMMatchLink(CartographyRelSchema):
    """
    MatchLink: (:ProxmoxPool)-[:CONTAINS_VM]->(:ProxmoxVM)

    Connects pools to the VMs they contain.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid"),  # Integer VMID
        }
    )
    source_node_label: str = "ProxmoxPool"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "poolid": PropertyRef("pool_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_VM"
    properties: ProxmoxPoolToVMMatchLinkProperties = (
        ProxmoxPoolToVMMatchLinkProperties()
    )


@dataclass(frozen=True)
class ProxmoxPoolToStorageMatchLinkProperties(CartographyRelProperties):
    """
    Properties for pool to storage CONTAINS_STORAGE relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxPoolToStorageMatchLink(CartographyRelSchema):
    """
    MatchLink: (:ProxmoxPool)-[:CONTAINS_STORAGE]->(:ProxmoxStorage)

    Connects pools to the storage resources they contain.
    """

    target_node_label: str = "ProxmoxStorage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("storage_id"),  # Storage ID
        }
    )
    source_node_label: str = "ProxmoxPool"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "poolid": PropertyRef("pool_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_STORAGE"
    properties: ProxmoxPoolToStorageMatchLinkProperties = (
        ProxmoxPoolToStorageMatchLinkProperties()
    )
