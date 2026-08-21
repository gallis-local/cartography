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
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import CERTIFICATE


@dataclass(frozen=True)
class OpenVASTLSCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The GVM UUID of this TLS certificate asset."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="The certificate's display name."
    )
    subject: PropertyRef = PropertyRef(
        "subject", description="Certificate subject distinguished name."
    )
    issuer: PropertyRef = PropertyRef(
        "issuer", description="Certificate issuer distinguished name."
    )
    not_before: PropertyRef = PropertyRef(
        "not_before", description="Certificate validity start date."
    )
    not_after: PropertyRef = PropertyRef(
        "not_after", description="Certificate validity end date."
    )
    serial: PropertyRef = PropertyRef(
        "serial", description="Certificate serial number."
    )
    fingerprint: PropertyRef = PropertyRef(
        "fingerprint", description="Certificate fingerprint hash."
    )
    certificate_format: PropertyRef = PropertyRef(
        "certificate_format",
        description="Encoding format of the certificate (e.g. DER, PEM).",
    )
    key_type: PropertyRef = PropertyRef(
        "key_type", description="Public key algorithm (e.g. RSA, EC)."
    )
    key_bits: PropertyRef = PropertyRef(
        "key_bits", description="Public key size in bits."
    )
    activation_time: PropertyRef = PropertyRef(
        "activation_time",
        description="When GVM first observed this certificate in use.",
    )
    expiry_time: PropertyRef = PropertyRef(
        "expiry_time",
        description="When GVM last observed this certificate in use, or its expiry.",
    )
    source_type: PropertyRef = PropertyRef(
        "source_type",
        description="How GVM discovered this certificate (e.g. via a host scan).",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Certificate status as reported by GVM (e.g. valid, expired).",
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
