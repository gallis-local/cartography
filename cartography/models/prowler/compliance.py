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


@dataclass(frozen=True)
class ProwlerComplianceAssessmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Provider-scoped identifier of the assessment, built as "
            "`<provider id>:<compliance id>`. The compliance framework is "
            "assessed once per provider, so the raw compliance id alone would "
            "collide across providers."
        ),
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Prowler compliance assessment was last seen.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "PROWLER_TENANT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description=(
            "Identifier of the Prowler tenant that owns this compliance assessment."
        ),
    )
    compliance_id: PropertyRef = PropertyRef(
        "compliance_id",
        extra_index=True,
        description=(
            "Prowler identifier of the compliance framework, for example `cis_2.0_aws`."
        ),
    )
    framework: PropertyRef = PropertyRef(
        "framework",
        extra_index=True,
        description="Name of the compliance framework, for example `CIS`.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Version of the compliance framework, for example `2.0`.",
    )
    requirements_passed: PropertyRef = PropertyRef(
        "requirements_passed",
        description="Number of framework requirements the provider passed.",
    )
    requirements_failed: PropertyRef = PropertyRef(
        "requirements_failed",
        extra_index=True,
        description="Number of framework requirements the provider failed.",
    )
    requirements_manual: PropertyRef = PropertyRef(
        "requirements_manual",
        description=(
            "Number of framework requirements Prowler cannot evaluate "
            "automatically and that need manual review."
        ),
    )
    total_requirements: PropertyRef = PropertyRef(
        "total_requirements",
        description="Total number of requirements in the framework.",
    )
    provider_id: PropertyRef = PropertyRef(
        "provider_id",
        extra_index=True,
        description="UUID of the Prowler provider this assessment covers.",
    )


@dataclass(frozen=True)
class ProwlerComplianceAssessmentToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this ownership relationship.",
    )


@dataclass(frozen=True)
class ProwlerComplianceAssessmentToTenantRel(CartographyRelSchema):
    """Links a Prowler tenant to one of its compliance assessments."""

    target_node_label: str = "ProwlerTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "PROWLER_TENANT_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Prowler tenant.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProwlerComplianceAssessmentToTenantRelProperties = (
        ProwlerComplianceAssessmentToTenantRelProperties()
    )


@dataclass(frozen=True)
class ProwlerComplianceAssessmentToProviderRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this assessment.",
    )


@dataclass(frozen=True)
class ProwlerComplianceAssessmentToProviderRel(CartographyRelSchema):
    """Links a compliance assessment to the Prowler provider it evaluates."""

    target_node_label: str = "ProwlerProvider"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "provider_id",
                description="UUID of the assessed Prowler provider.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSESSES"
    properties: ProwlerComplianceAssessmentToProviderRelProperties = (
        ProwlerComplianceAssessmentToProviderRelProperties()
    )


@dataclass(frozen=True)
class ProwlerComplianceAssessmentSchema(CartographyNodeSchema):
    """One Prowler provider's posture against one compliance framework.

    Prowler evaluates each provider against every framework it supports (CIS,
    SOC 2, ISO 27001, PCI DSS, HIPAA and others), and reports how many of that
    framework's requirements passed, failed, or need manual review. The counts
    reflect the provider's most recent completed scan.

    `requirements_manual` is not a failure: those are controls Prowler cannot
    evaluate automatically, so a framework is only fully satisfied when
    `requirements_failed` is 0 and the manual controls have been reviewed
    out-of-band.
    """

    label: str = "ProwlerComplianceAssessment"
    properties: ProwlerComplianceAssessmentNodeProperties = (
        ProwlerComplianceAssessmentNodeProperties()
    )
    sub_resource_relationship: ProwlerComplianceAssessmentToTenantRel = (
        ProwlerComplianceAssessmentToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProwlerComplianceAssessmentToProviderRel(),
        ],
    )
