"""
Data models for Proxmox API tokens.

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
# ProxmoxAPIToken Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxAPITokenNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxAPIToken node.

    Represents API tokens for authentication in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tokenid: PropertyRef = PropertyRef("tokenid", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    userid: PropertyRef = PropertyRef("userid")  # Parent user ID
    expire: PropertyRef = PropertyRef("expire")  # Expiration timestamp
    privsep: PropertyRef = PropertyRef("privsep")  # Privilege separation
    comment: PropertyRef = PropertyRef("comment")


@dataclass(frozen=True)
class ProxmoxAPITokenToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxAPIToken to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxAPITokenToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxAPIToken)-[:RESOURCE]->(:ProxmoxCluster)

    API tokens belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxAPITokenToClusterRelProperties = ProxmoxAPITokenToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxAPITokenToUserRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxAPIToken to ProxmoxUser.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxAPITokenToUserRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxAPIToken)-[:BELONGS_TO]->(:ProxmoxUser)

    API tokens belong to users.
    """

    target_node_label: str = "ProxmoxUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "userid": PropertyRef("userid"),
            "cluster_id": PropertyRef("cluster_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: ProxmoxAPITokenToUserRelProperties = ProxmoxAPITokenToUserRelProperties()


@dataclass(frozen=True)
class ProxmoxAPITokenSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxAPIToken.

    API tokens for authentication and authorization.
    """

    label: str = "ProxmoxAPIToken"
    properties: ProxmoxAPITokenNodeProperties = ProxmoxAPITokenNodeProperties()
    sub_resource_relationship: ProxmoxAPITokenToClusterRel = ProxmoxAPITokenToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxAPITokenToUserRel(),
        ]
    )
