"""
Data models for Proxmox API tokens.

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
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import API_KEY

# ProxmoxAPIToken Node Schema


@dataclass(frozen=True)
class ProxmoxAPITokenNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxAPIToken node.

    Represents API tokens for authentication in Proxmox VE.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this token, in the form `{cluster_id}/user/{userid}/token/{tokenid}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tokenid: PropertyRef = PropertyRef(
        "tokenid",
        extra_index=True,
        description="Name of the token within its owning user. Together with the user it forms the login `user@realm!tokenid`.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    userid: PropertyRef = PropertyRef(
        "userid", description="`user@realm` of the account that owns this token."
    )
    expire: PropertyRef = PropertyRef(
        "expire",
        description="Token expiration as a Unix epoch timestamp in seconds. 0 means the token never expires.",
    )
    privsep: PropertyRef = PropertyRef(
        "privsep",
        description="True when privilege separation is enabled, so the token only holds permissions granted to the token itself rather than everything its owner can do.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment stored on the token."
    )


@dataclass(frozen=True)
class ProxmoxAPITokenToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxAPITokenToClusterRel(CartographyRelSchema):
    """
    API tokens belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxAPITokenToClusterRelProperties = (
        ProxmoxAPITokenToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxAPITokenToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxAPITokenToUserRel(CartographyRelSchema):
    """
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
    rel_label: str = "OWNED_BY"
    properties: ProxmoxAPITokenToUserRelProperties = (
        ProxmoxAPITokenToUserRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxAPITokenSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxAPIToken.

    API tokens for authentication and authorization.
    """

    label: str = "ProxmoxAPIToken"
    properties: ProxmoxAPITokenNodeProperties = ProxmoxAPITokenNodeProperties()
    sub_resource_relationship: ProxmoxAPITokenToClusterRel = (
        ProxmoxAPITokenToClusterRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxAPITokenToUserRel(),
        ]
    )
