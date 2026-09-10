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
class ProwlerResourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Prowler-assigned UUID of the resource.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Prowler resource was last seen.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "PROWLER_TENANT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Identifier of the Prowler tenant that owns this resource.",
    )
    uid: PropertyRef = PropertyRef(
        "uid",
        extra_index=True,
        description=(
            "Provider-native identifier of the resource, such as an AWS ARN. This "
            "is the value to join on when correlating with cloud inventory."
        ),
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Provider-native name of the resource.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        extra_index=True,
        description="Cloud region the resource lives in.",
    )
    service: PropertyRef = PropertyRef(
        "service",
        extra_index=True,
        description="Provider service that owns the resource, for example `s3`.",
    )
    resource_type: PropertyRef = PropertyRef(
        "resource_type",
        extra_index=True,
        description="Provider resource type, for example `AwsS3Bucket`.",
    )
    partition: PropertyRef = PropertyRef(
        "partition",
        description="Cloud partition of the resource, for example `aws` or `aws-us-gov`.",
    )
    groups: PropertyRef = PropertyRef(
        "groups",
        description="Prowler resource groups the resource belongs to, for example `storage`.",
    )
    failed_findings_count: PropertyRef = PropertyRef(
        "failed_findings_count",
        description="Number of failing Prowler findings currently attached to the resource.",
    )
    tag_keys: PropertyRef = PropertyRef(
        "tag_keys",
        extra_index=True,
        description="Sorted list of the resource's tag keys.",
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Sorted list of the resource's tags rendered as `key=value` strings.",
    )
    provider_id: PropertyRef = PropertyRef(
        "provider_id",
        extra_index=True,
        description="UUID of the Prowler provider that owns the resource.",
    )
    inserted_at: PropertyRef = PropertyRef(
        "inserted_at",
        description="Timestamp when Prowler first recorded the resource.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when Prowler last modified the resource.",
    )


@dataclass(frozen=True)
class ProwlerResourceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this ownership relationship.",
    )


@dataclass(frozen=True)
class ProwlerResourceToTenantRel(CartographyRelSchema):
    """Links a Prowler tenant to one of its scanned resources."""

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
    properties: ProwlerResourceToTenantRelProperties = (
        ProwlerResourceToTenantRelProperties()
    )


@dataclass(frozen=True)
class ProwlerResourceToProviderRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this resource ownership.",
    )


@dataclass(frozen=True)
class ProwlerResourceToProviderRel(CartographyRelSchema):
    """Links a Prowler resource to the provider it was discovered in."""

    target_node_label: str = "ProwlerProvider"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "provider_id",
                description="UUID of the Prowler provider that owns the resource.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProwlerResourceToProviderRelProperties = (
        ProwlerResourceToProviderRelProperties()
    )


@dataclass(frozen=True)
class ProwlerResourceSchema(CartographyNodeSchema):
    """A cloud resource that Prowler evaluated during a scan.

    The `uid` property holds the provider-native identifier (an ARN for AWS), which
    is the value to join on when correlating Prowler findings with resources
    ingested by Cartography's own cloud modules.
    """

    label: str = "ProwlerResource"
    properties: ProwlerResourceNodeProperties = ProwlerResourceNodeProperties()
    sub_resource_relationship: ProwlerResourceToTenantRel = ProwlerResourceToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProwlerResourceToProviderRel(),
        ],
    )
