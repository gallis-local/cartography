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
class ProwlerProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Prowler-assigned UUID of the provider.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Prowler provider was last seen.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "PROWLER_TENANT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Identifier of the Prowler tenant that owns this provider.",
    )
    uid: PropertyRef = PropertyRef(
        "uid",
        extra_index=True,
        description=(
            "Provider-native account identifier, such as an AWS account ID, an "
            "Azure subscription ID, a GCP project ID, or a Kubernetes context name."
        ),
    )
    provider_type: PropertyRef = PropertyRef(
        "provider_type",
        extra_index=True,
        description=(
            "Cloud or platform type scanned by Prowler, for example `aws`, "
            "`azure`, `gcp`, `kubernetes`, or `github`."
        ),
    )
    alias: PropertyRef = PropertyRef(
        "alias",
        description="Human-readable alias assigned to the provider in Prowler.",
    )
    available: PropertyRef = PropertyRef(
        "available",
        description=(
            "Whether Prowler considers the underlying account reachable. False "
            "means Prowler skips connection checks and scans for it."
        ),
    )
    connected: PropertyRef = PropertyRef(
        "connected",
        description="Whether Prowler's most recent credential check succeeded.",
    )
    connection_last_checked_at: PropertyRef = PropertyRef(
        "connection_last_checked_at",
        description="Timestamp of Prowler's most recent credential check.",
    )
    is_dynamic: PropertyRef = PropertyRef(
        "is_dynamic",
        description="Whether the provider was discovered dynamically by Prowler.",
    )
    is_imported: PropertyRef = PropertyRef(
        "is_imported",
        description="Whether the provider's findings were imported rather than scanned.",
    )
    inserted_at: PropertyRef = PropertyRef(
        "inserted_at",
        description="Timestamp when the provider was created in Prowler.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the provider was last modified in Prowler.",
    )
    aws_account_id: PropertyRef = PropertyRef(
        "aws_account_id",
        extra_index=True,
        description=(
            "AWS account ID scanned by this provider. Only set when "
            "`provider_type` is `aws`."
        ),
    )
    azure_subscription_id: PropertyRef = PropertyRef(
        "azure_subscription_id",
        extra_index=True,
        description=(
            "Azure subscription ID scanned by this provider. Only set when "
            "`provider_type` is `azure`."
        ),
    )
    gcp_project_id: PropertyRef = PropertyRef(
        "gcp_project_id",
        extra_index=True,
        description=(
            "GCP project ID scanned by this provider. Only set when "
            "`provider_type` is `gcp`."
        ),
    )
    kubernetes_cluster_name: PropertyRef = PropertyRef(
        "kubernetes_cluster_name",
        extra_index=True,
        description=(
            "Kubernetes context name scanned by this provider. Only set when "
            "`provider_type` is `kubernetes`."
        ),
    )


@dataclass(frozen=True)
class ProwlerProviderToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this ownership relationship.",
    )


@dataclass(frozen=True)
class ProwlerProviderToTenantRel(CartographyRelSchema):
    """Links a Prowler tenant to one of its configured providers."""

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
    properties: ProwlerProviderToTenantRelProperties = (
        ProwlerProviderToTenantRelProperties()
    )


@dataclass(frozen=True)
class ProwlerProviderToCloudAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this account association.",
    )


@dataclass(frozen=True)
class ProwlerProviderToAWSAccountRel(CartographyRelSchema):
    """Links a Prowler provider to the AWS account it scans."""

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "aws_account_id",
                description="AWS account ID scanned by this Prowler provider.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANS"
    properties: ProwlerProviderToCloudAccountRelProperties = (
        ProwlerProviderToCloudAccountRelProperties()
    )


@dataclass(frozen=True)
class ProwlerProviderToAzureSubscriptionRel(CartographyRelSchema):
    """Links a Prowler provider to the Azure subscription it scans."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "azure_subscription_id",
                description="Azure subscription ID scanned by this Prowler provider.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANS"
    properties: ProwlerProviderToCloudAccountRelProperties = (
        ProwlerProviderToCloudAccountRelProperties()
    )


@dataclass(frozen=True)
class ProwlerProviderToGCPProjectRel(CartographyRelSchema):
    """Links a Prowler provider to the GCP project it scans."""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "gcp_project_id",
                description="GCP project ID scanned by this Prowler provider.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANS"
    properties: ProwlerProviderToCloudAccountRelProperties = (
        ProwlerProviderToCloudAccountRelProperties()
    )


@dataclass(frozen=True)
class ProwlerProviderToKubernetesClusterRel(CartographyRelSchema):
    """Links a Prowler provider to the Kubernetes cluster it scans."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef(
                "kubernetes_cluster_name",
                description=(
                    "Kubernetes context name scanned by this Prowler provider. "
                    "Cartography derives KubernetesCluster.name from the same "
                    "kubeconfig context, so the two values line up."
                ),
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANS"
    properties: ProwlerProviderToCloudAccountRelProperties = (
        ProwlerProviderToCloudAccountRelProperties()
    )


@dataclass(frozen=True)
class ProwlerProviderSchema(CartographyNodeSchema):
    """A cloud account, subscription, project, or cluster configured for scanning in Prowler.

    When the matching cloud module has also been synced, the provider is attached
    to the existing `AWSAccount`, `AzureSubscription`, `GCPProject`, or
    `KubernetesCluster` node with a `SCANS` relationship. Those edges are
    best-effort: they are created only when the corresponding cloud node is
    already in the graph, so Prowler can be synced on its own.
    """

    label: str = "ProwlerProvider"
    properties: ProwlerProviderNodeProperties = ProwlerProviderNodeProperties()
    sub_resource_relationship: ProwlerProviderToTenantRel = ProwlerProviderToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProwlerProviderToAWSAccountRel(),
            ProwlerProviderToAzureSubscriptionRel(),
            ProwlerProviderToGCPProjectRel(),
            ProwlerProviderToKubernetesClusterRel(),
        ],
    )
