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
from cartography.models.ontology.labels import CERTIFICATE

# ProxmoxCertificate Node Schema


@dataclass(frozen=True)
class ProxmoxCertificateNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxCertificate node.

    Represents SSL/TLS certificates used by Proxmox nodes.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this certificate, in the form `{cluster_id}/node/{node}/cert/{filename}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    node_id: PropertyRef = PropertyRef(
        "node_id", description="Id of the `ProxmoxNode` that serves this certificate."
    )
    filename: PropertyRef = PropertyRef(
        "filename",
        extra_index=True,
        description="Name of the certificate file on the node, e.g. `pve-ssl.pem` or `pveproxy-ssl.pem`.",
    )
    fingerprint: PropertyRef = PropertyRef(
        "fingerprint",
        extra_index=True,
        description="Fingerprint of the certificate as reported by Proxmox.",
    )
    issuer: PropertyRef = PropertyRef(
        "issuer",
        description="Distinguished name of the certificate authority that issued the certificate.",
    )
    subject: PropertyRef = PropertyRef(
        "subject", description="Subject distinguished name of the certificate."
    )
    san: PropertyRef = PropertyRef(
        "san", description="Subject Alternative Names the certificate is valid for."
    )
    notbefore: PropertyRef = PropertyRef(
        "notbefore",
        description="Start of the certificate validity window as a Unix epoch timestamp in seconds.",
    )
    notafter: PropertyRef = PropertyRef(
        "notafter",
        extra_index=True,
        description="End of the certificate validity window as a Unix epoch timestamp in seconds.",
    )
    public_key_type: PropertyRef = PropertyRef(
        "public_key_type", description="Public key algorithm, e.g. `rsa` or `ecdsa`."
    )
    public_key_bits: PropertyRef = PropertyRef(
        "public_key_bits", description="Size of the public key in bits."
    )
    pem: PropertyRef = PropertyRef(
        "pem", description="The certificate itself, PEM encoded."
    )
    # Computed expiration properties for easy querying
    expires_in_days: PropertyRef = PropertyRef(
        "expires_in_days",
        extra_index=True,
        description="Whole days from the time of the sync until `notafter`. Negative once the certificate has expired.",
    )
    is_expired: PropertyRef = PropertyRef(
        "is_expired",
        extra_index=True,
        description="True when `notafter` was already in the past at the time of the sync.",
    )
    expires_soon: PropertyRef = PropertyRef(
        "expires_soon",
        extra_index=True,
        description="True when the certificate is still valid but expires within 30 days of the sync.",
    )


@dataclass(frozen=True)
class ProxmoxCertificateToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxCertificateToClusterRel(CartographyRelSchema):
    """
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CERTIFICATE])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxCertificateToNodeRel(),
        ]
    )
