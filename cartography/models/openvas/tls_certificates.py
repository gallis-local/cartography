"""
Data model for OpenVAS TLS certificates.
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
from cartography.models.ontology.labels import CERTIFICATE


@dataclass(frozen=True)
class OpenVASTLSCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The GVM UUID of this TLS certificate asset."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef(
        "OPENVAS_INSTANCE_ID",
        set_in_kwargs=True,
        description="Id of the OpenVASInstance (GVM deployment) this resource belongs to.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="The certificate's display name, which gvmd sets to its SHA-256 fingerprint.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment set on the certificate."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When GVM first recorded this certificate."
    )
    modification_time: PropertyRef = PropertyRef(
        "modification_time",
        description="When this certificate record was last modified.",
    )
    subject_dn: PropertyRef = PropertyRef(
        "subject_dn", description="Certificate subject distinguished name."
    )
    issuer_dn: PropertyRef = PropertyRef(
        "issuer_dn", description="Certificate issuer distinguished name."
    )
    serial: PropertyRef = PropertyRef(
        "serial", description="Certificate serial number, in hex."
    )
    sha256_fingerprint: PropertyRef = PropertyRef(
        "sha256_fingerprint",
        extra_index=True,
        description="SHA-256 fingerprint of the certificate.",
    )
    md5_fingerprint: PropertyRef = PropertyRef(
        "md5_fingerprint", description="MD5 fingerprint of the certificate."
    )
    certificate_format: PropertyRef = PropertyRef(
        "certificate_format",
        description="Encoding format of the certificate data (DER, PEM or unknown).",
    )
    activation_time: PropertyRef = PropertyRef(
        "activation_time",
        description="Start of the certificate's validity period (notBefore).",
    )
    expiration_time: PropertyRef = PropertyRef(
        "expiration_time",
        description="End of the certificate's validity period (notAfter).",
    )
    last_seen: PropertyRef = PropertyRef(
        "last_seen", description="When GVM last observed this certificate in use."
    )
    valid: PropertyRef = PropertyRef(
        "valid",
        description="Whether GVM considers the certificate currently valid.",
    )
    trust: PropertyRef = PropertyRef(
        "trust", description="GVM's trust level for the certificate, as an integer."
    )
    time_status: PropertyRef = PropertyRef(
        "time_status",
        extra_index=True,
        description="Validity status over time as reported by GVM (valid, expired, inactive, unknown).",
    )


@dataclass(frozen=True)
class OpenVASTLSCertificateToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASTLSCertificate)
class OpenVASTLSCertificateToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this TLS certificate asset."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASTLSCertificateToInstanceRelProperties = (
        OpenVASTLSCertificateToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASTLSCertificateSchema(CartographyNodeSchema):
    """A TLS certificate discovered by GVM's TLS certificate asset scanning."""

    label: str = "OpenVASTLSCertificate"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CERTIFICATE])
    properties: OpenVASTLSCertificateNodeProperties = (
        OpenVASTLSCertificateNodeProperties()
    )
    sub_resource_relationship: OpenVASTLSCertificateToInstanceRel = (
        OpenVASTLSCertificateToInstanceRel()
    )


@dataclass(frozen=True)
class OpenVASCertificateToHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    ports: PropertyRef = PropertyRef(
        "ports",
        description="Ports of this host the certificate was observed being served on.",
    )


@dataclass(frozen=True)
# (:OpenVASTLSCertificate)-[:CERTIFICATE_FOR]->(:OpenVASHost)
class OpenVASCertificateToHostMatchLink(CartographyRelSchema):
    """
    Connects `OpenVASTLSCertificate` to the `OpenVASHost` that served it.

    gvmd reports the observation sites of a certificate in its own <sources>
    block, keyed by host IP -- a separate read from the host sync, hence a
    MatchLink. The certificate's <name> is its SHA-256 fingerprint, so the
    earlier "match the certificate name against a host ip or hostname" heuristic
    could never match anything, and every certificate sat unlinked.
    """

    source_node_label: str = "OpenVASTLSCertificate"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("certificate_id")},
    )
    target_node_label: str = "OpenVASHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ip": PropertyRef("host_ip")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CERTIFICATE_FOR"
    properties: OpenVASCertificateToHostRelProperties = (
        OpenVASCertificateToHostRelProperties()
    )
