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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    subject: PropertyRef = PropertyRef("subject")
    issuer: PropertyRef = PropertyRef("issuer")
    not_before: PropertyRef = PropertyRef("not_before")
    not_after: PropertyRef = PropertyRef("not_after")
    serial: PropertyRef = PropertyRef("serial")
    fingerprint: PropertyRef = PropertyRef("fingerprint")
    certificate_format: PropertyRef = PropertyRef("certificate_format")
    key_type: PropertyRef = PropertyRef("key_type")
    key_bits: PropertyRef = PropertyRef("key_bits")
    activation_time: PropertyRef = PropertyRef("activation_time")
    expiry_time: PropertyRef = PropertyRef("expiry_time")
    source_type: PropertyRef = PropertyRef("source_type")
    status: PropertyRef = PropertyRef("status")


@dataclass(frozen=True)
class OpenVASTLSCertificateToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASTLSCertificate)
@dataclass(frozen=True)
class OpenVASTLSCertificateToInstanceRel(CartographyRelSchema):
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
    label: str = "OpenVASTLSCertificate"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CERTIFICATE])
    properties: OpenVASTLSCertificateNodeProperties = (
        OpenVASTLSCertificateNodeProperties()
    )
    sub_resource_relationship: OpenVASTLSCertificateToInstanceRel = (
        OpenVASTLSCertificateToInstanceRel()
    )
