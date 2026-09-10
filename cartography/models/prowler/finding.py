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
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class ProwlerFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Prowler-assigned UUID of the finding.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Prowler finding was last seen.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "PROWLER_TENANT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Identifier of the Prowler tenant that owns this finding.",
    )
    uid: PropertyRef = PropertyRef(
        "uid",
        extra_index=True,
        description=(
            "Prowler's deterministic finding identifier, of the form "
            "`prowler-{provider}-{check_id}-{account}-{region}-{resource}`. Stable "
            "across scans, so it identifies the same issue over time."
        ),
    )
    check_id: PropertyRef = PropertyRef(
        "check_id",
        extra_index=True,
        description="Prowler check that produced the finding, for example `s3_bucket_public_access`.",
    )
    check_title: PropertyRef = PropertyRef(
        "check_title",
        description="Human-readable title of the Prowler check.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of what the Prowler check evaluates.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Outcome of the check: `PASS`, `FAIL`, or `MANUAL`.",
    )
    status_extended: PropertyRef = PropertyRef(
        "status_extended",
        description="Human-readable explanation of why the check produced this status.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description=(
            "Severity reported by Prowler: `critical`, `high`, `medium`, `low`, "
            "or `informational`."
        ),
    )
    delta: PropertyRef = PropertyRef(
        "delta",
        extra_index=True,
        description=(
            "How the finding changed relative to the previous scan: `new`, "
            "`changed`, or unset when unchanged."
        ),
    )
    service_name: PropertyRef = PropertyRef(
        "service_name",
        extra_index=True,
        description="Provider service the check applies to, for example `s3`.",
    )
    resource_type: PropertyRef = PropertyRef(
        "resource_type",
        extra_index=True,
        description="Provider resource type the check applies to, for example `AwsS3Bucket`.",
    )
    resource_groups: PropertyRef = PropertyRef(
        "resource_groups",
        extra_index=True,
        description="Prowler resource group of the check, for example `storage`.",
    )
    categories: PropertyRef = PropertyRef(
        "categories",
        description="Prowler categories assigned to the check, for example `internet-exposed`.",
    )
    compliance_frameworks: PropertyRef = PropertyRef(
        "compliance_frameworks",
        extra_index=True,
        description=(
            "Sorted names of the compliance frameworks that map to this check, "
            "for example `CIS-2.0`."
        ),
    )
    risk: PropertyRef = PropertyRef(
        "risk",
        description="Prowler's description of the risk the check guards against.",
    )
    remediation_text: PropertyRef = PropertyRef(
        "remediation_text",
        description="Prowler's recommended remediation for the finding.",
    )
    remediation_url: PropertyRef = PropertyRef(
        "remediation_url",
        description="Link to Prowler's remediation guidance for the check.",
    )
    remediation_cli: PropertyRef = PropertyRef(
        "remediation_cli",
        description="Provider CLI command that remediates the finding, when Prowler supplies one.",
    )
    remediation_terraform: PropertyRef = PropertyRef(
        "remediation_terraform",
        description="Terraform snippet that remediates the finding, when Prowler supplies one.",
    )
    muted: PropertyRef = PropertyRef(
        "muted",
        extra_index=True,
        description="Whether the finding is muted in Prowler.",
    )
    muted_reason: PropertyRef = PropertyRef(
        "muted_reason",
        description="Reason recorded in Prowler for muting the finding.",
    )
    triage_status: PropertyRef = PropertyRef(
        "triage_status",
        extra_index=True,
        description=(
            "Triage state in Prowler: `open`, `under_review`, `remediating`, "
            "`resolved`, `risk_accepted`, `false_positive`, or `reopened`."
        ),
    )
    cve_ids: PropertyRef = PropertyRef(
        "cve_ids",
        description="Canonical CVE identifiers referenced by the finding, when any.",
    )
    scan_id: PropertyRef = PropertyRef(
        "scan_id",
        extra_index=True,
        description="UUID of the Prowler scan that produced the finding.",
    )
    resource_ids: PropertyRef = PropertyRef(
        "resource_ids",
        description="UUIDs of the Prowler resources the finding applies to.",
    )
    resource_uids: PropertyRef = PropertyRef(
        "resource_uids",
        extra_index=True,
        description=(
            "Provider-native identifiers, such as ARNs, of the resources the "
            "finding applies to."
        ),
    )
    first_seen_at: PropertyRef = PropertyRef(
        "first_seen_at",
        description="Timestamp when Prowler first observed the finding.",
    )
    inserted_at: PropertyRef = PropertyRef(
        "inserted_at",
        description="Timestamp when Prowler recorded this occurrence of the finding.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when Prowler last modified the finding.",
    )


@dataclass(frozen=True)
class ProwlerFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this ownership relationship.",
    )


@dataclass(frozen=True)
class ProwlerFindingToTenantRel(CartographyRelSchema):
    """Links a Prowler tenant to one of its findings."""

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
    properties: ProwlerFindingToTenantRelProperties = (
        ProwlerFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class ProwlerFindingToScanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this finding in the scan.",
    )


@dataclass(frozen=True)
class ProwlerFindingToScanRel(CartographyRelSchema):
    """Links a Prowler finding to the scan that produced it."""

    target_node_label: str = "ProwlerScan"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "scan_id",
                description="UUID of the Prowler scan that produced the finding.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTIFIED"
    properties: ProwlerFindingToScanRelProperties = ProwlerFindingToScanRelProperties()


@dataclass(frozen=True)
class ProwlerFindingToResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this finding against the resource.",
    )


@dataclass(frozen=True)
class ProwlerFindingToResourceRel(CartographyRelSchema):
    """Links a Prowler finding to each resource it was raised against."""

    target_node_label: str = "ProwlerResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "resource_ids",
                one_to_many=True,
                description="UUIDs of the Prowler resources the finding applies to.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: ProwlerFindingToResourceRelProperties = (
        ProwlerFindingToResourceRelProperties()
    )


@dataclass(frozen=True)
class ProwlerFindingSchema(CartographyNodeSchema):
    """The outcome of one Prowler check against one resource.

    Findings carry the [`SecurityIssue`](#ontology-securityissue) ontology label so
    they can be compared with security issues from other providers. Note that
    Prowler records passing checks too: filter on `status = 'FAIL'` to look at
    failures only.
    """

    label: str = "ProwlerFinding"
    properties: ProwlerFindingNodeProperties = ProwlerFindingNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
    sub_resource_relationship: ProwlerFindingToTenantRel = ProwlerFindingToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProwlerFindingToScanRel(),
            ProwlerFindingToResourceRel(),
        ],
    )
