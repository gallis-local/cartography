"""
Data models for Proxmox SSL/TLS certificates.

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

# ProxmoxCertificate Node Schema

@dataclass(frozen=True)
class ProxmoxCertificateNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxCertificate node.

    Represents SSL/TLS certificates used by Proxmox nodes.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    node_id: PropertyRef = PropertyRef("node_id")
    filename: PropertyRef = PropertyRef("filename", extra_index=True)
    fingerprint: PropertyRef = PropertyRef("fingerprint", extra_index=True)
    issuer: PropertyRef = PropertyRef("issuer")
    subject: PropertyRef = PropertyRef("subject")
    san: PropertyRef = PropertyRef("san")
    notbefore: PropertyRef = PropertyRef("notbefore")
    notafter: PropertyRef = PropertyRef("notafter", extra_index=True)
    public_key_type: PropertyRef = PropertyRef("public_key_type")
    public_key_bits: PropertyRef = PropertyRef("public_key_bits")
    pem: PropertyRef = PropertyRef("pem")
    # Computed expiration properties for easy querying
    expires_in_days: PropertyRef = PropertyRef(
        "expires_in_days", extra_index=True
    )
    is_expired: PropertyRef = PropertyRef(
        "is_expired", extra_index=True
    )
    expires_soon: PropertyRef = PropertyRef(
        "expires_soon", extra_index=True
    )

@dataclass(frozen=True)
class ProxmoxCertificateToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxCertificateToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxCertificate)

    Certificates belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxCertificateToClusterRelProperties = (
        ProxmoxCertificateToClusterRelProperties()
    )

@dataclass(frozen=True)
class ProxmoxCertificateToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxCertificateToNodeRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNode)-[:HAS_CERTIFICATE]->(:ProxmoxCertificate)

    Nodes use SSL certificates.
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("node_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CERTIFICATE"
    properties: ProxmoxCertificateToNodeRelProperties = (
        ProxmoxCertificateToNodeRelProperties()
    )

@dataclass(frozen=True)
class ProxmoxCertificateSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxCertificate.

    SSL/TLS certificates used for HTTPS and cluster communication.
    """

    label: str = "ProxmoxCertificate"
    properties: ProxmoxCertificateNodeProperties = ProxmoxCertificateNodeProperties()
    sub_resource_relationship: ProxmoxCertificateToClusterRel = (
        ProxmoxCertificateToClusterRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Certificate"])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxCertificateToNodeRel(),
        ]
    )
