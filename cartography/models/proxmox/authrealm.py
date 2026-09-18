"""
Data models for Proxmox authentication realms.

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
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import IDENTITY_PROVIDER

# ProxmoxAuthRealm Node Schema


@dataclass(frozen=True)
class ProxmoxAuthRealmNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxAuthRealm node.

    Represents authentication realms (PAM, LDAP, AD, etc.) in Proxmox VE.
    """

    id: PropertyRef = PropertyRef(
        "id", description="Cluster-scoped identifier for this authentication realm."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    realm: PropertyRef = PropertyRef(
        "realm",
        extra_index=True,
        description="Realm name, used as the suffix of `userid` values, e.g. `pam` in `root@pam`.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Realm backend type: `pam`, `pve`, `ldap`, `ad` or `openid`.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment stored on the realm."
    )
    default: PropertyRef = PropertyRef(
        "default",
        description="True when this realm is preselected on the Proxmox login form.",
    )
    tfa: PropertyRef = PropertyRef(
        "tfa",
        description="Realm-wide second factor required for login, e.g. `oath` or `yubico`. Null when the realm enforces no second factor of its own.",
    )


@dataclass(frozen=True)
class ProxmoxAuthRealmToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxAuthRealmToClusterRel(CartographyRelSchema):
    """
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
    properties: ProxmoxAuthRealmToClusterRelProperties = (
        ProxmoxAuthRealmToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxAuthRealmSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxAuthRealm.

    Authentication realms for user authentication.
    """

    label: str = "ProxmoxAuthRealm"
    properties: ProxmoxAuthRealmNodeProperties = ProxmoxAuthRealmNodeProperties()
    sub_resource_relationship: ProxmoxAuthRealmToClusterRel = (
        ProxmoxAuthRealmToClusterRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IDENTITY_PROVIDER])
