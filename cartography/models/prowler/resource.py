from dataclasses import dataclass
from dataclasses import field
from dataclasses import make_dataclass

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
    # Not RESOURCE: that label is the tenant-ownership edge, and a second one
    # into this node would make (:ProwlerTenant)-[:RESOURCE]->() ambiguous.
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: ProwlerResourceToProviderRelProperties = (
        ProwlerResourceToProviderRelProperties()
    )


@dataclass(frozen=True)
class ProwlerResourceToCloudResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this resource correlation.",
    )


# Cartography node labels whose `arn` property can be joined against a Prowler
# AWS resource `uid`. Every entry is a label whose `arn` is declared with
# `extra_index=True`, so each correlation is an index seek rather than a scan.
#
# Deliberately excluded:
#   - Labels with no `arn` property at all, which therefore cannot be joined:
#     AWSVpc, AWSEC2Subnet, AWSEC2SecurityGroup, AWSLoadBalancer (classic),
#     AWSAPIGatewayRestAPI, AWSEBSSnapshot. These are common Prowler check
#     targets, so their findings stay reachable only through the provider's
#     account-level SCANS edge until those models carry an ARN (see #1024).
#   - AWSInstanceProfile, whose `arn` is not indexed.
#   - AWSPrincipal, a shared extra label that AWSUser and AWSRole also carry,
#     which would double-link every IAM finding.
_AWS_ARN_TARGET_LABELS: tuple[str, ...] = (
    "AWSACMCertificate",
    "AWSCloudFrontDistribution",
    "AWSDynamoDBTable",
    "AWSEBSVolume",
    "AWSEC2Instance",
    "AWSECRRepository",
    "AWSECSCluster",
    "AWSECSService",
    "AWSEKSCluster",
    "AWSESDomain",
    "AWSEfsFileSystem",
    "AWSElasticacheCluster",
    "AWSGroup",
    "AWSKMSKey",
    "AWSLambda",
    "AWSLoadBalancerV2",
    "AWSRDSCluster",
    "AWSRDSInstance",
    "AWSRDSSnapshot",
    "AWSRole",
    "AWSS3Bucket",
    "AWSSNSTopic",
    "AWSSQSQueue",
    "AWSSSMParameter",
    "AWSSecretsManagerSecret",
    "AWSUser",
)


def _make_cloud_resource_rel(target_node_label: str) -> type[CartographyRelSchema]:
    """Build the REPRESENTS edge from a Prowler resource to one cloud node label.

    These are written as one schema per label rather than a single label-agnostic
    edge because a `CartographyRelSchema` needs a static `target_node_label`, and
    because a label-scoped match on an indexed `arn` is an index seek. Matching
    `arn` without a label would be a scan of every node in the graph.
    """
    return make_dataclass(
        f"ProwlerResourceTo{target_node_label}Rel",
        [
            ("target_node_label", str, field(default=target_node_label)),
            (
                "target_node_matcher",
                TargetNodeMatcher,
                field(
                    default=make_target_node_matcher(
                        {
                            "arn": PropertyRef(
                                "aws_uid",
                                description=(
                                    "ARN of the AWS resource this Prowler "
                                    "resource was scanned from."
                                ),
                            ),
                        },
                    ),
                ),
            ),
            ("direction", LinkDirection, field(default=LinkDirection.OUTWARD)),
            ("rel_label", str, field(default="REPRESENTS")),
            (
                "properties",
                ProwlerResourceToCloudResourceRelProperties,
                field(default=ProwlerResourceToCloudResourceRelProperties()),
            ),
        ],
        bases=(CartographyRelSchema,),
        frozen=True,
        namespace={
            "__doc__": (
                f"Links a Prowler resource to the `{target_node_label}` it was "
                "scanned from, matched on ARN."
            ),
        },
    )


PROWLER_RESOURCE_TO_CLOUD_RESOURCE_RELS: tuple[CartographyRelSchema, ...] = tuple(
    _make_cloud_resource_rel(label)() for label in _AWS_ARN_TARGET_LABELS
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
            *PROWLER_RESOURCE_TO_CLOUD_RESOURCE_RELS,
        ],
    )
