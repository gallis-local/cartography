"""
Data models for Proxmox authentication realms.

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
from cartography.models.core.relationships import TargetNodeMatcher

# ============================================================================
# ProxmoxAuthRealm Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxAuthRealmNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxAuthRealm node.

    Represents authentication realms (PAM, LDAP, AD, etc.) in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    realm: PropertyRef = PropertyRef("realm", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    type: PropertyRef = PropertyRef("type")  # pam, ldap, ad, pve, openid
    comment: PropertyRef = PropertyRef("comment")
    default: PropertyRef = PropertyRef("default")  # Is default realm
    tfa: PropertyRef = PropertyRef("tfa")  # Two-factor auth type (oath, yubico, etc.)


@dataclass(frozen=True)
class ProxmoxAuthRealmToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxAuthRealm to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxAuthRealmToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxAuthRealm)

    Auth realms belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxAuthRealmToClusterRelProperties = ProxmoxAuthRealmToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxAuthRealmSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxAuthRealm.

    Authentication realms for user authentication.
    """

    label: str = "ProxmoxAuthRealm"
    properties: ProxmoxAuthRealmNodeProperties = ProxmoxAuthRealmNodeProperties()
    sub_resource_relationship: ProxmoxAuthRealmToClusterRel = ProxmoxAuthRealmToClusterRel()
