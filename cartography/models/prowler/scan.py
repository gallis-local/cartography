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
class ProwlerScanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Prowler-assigned UUID of the scan.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Prowler scan was last seen.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "PROWLER_TENANT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Identifier of the Prowler tenant that owns this scan.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name assigned to the scan in Prowler.",
    )
    trigger: PropertyRef = PropertyRef(
        "trigger",
        extra_index=True,
        description="How the scan was started: `scheduled`, `manual`, or `imported`.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        extra_index=True,
        description=(
            "Lifecycle state of the scan: `available`, `scheduled`, `executing`, "
            "`completed`, `failed`, or `cancelled`."
        ),
    )
    unique_resource_count: PropertyRef = PropertyRef(
        "unique_resource_count",
        description="Number of distinct resources evaluated by the scan.",
    )
    progress: PropertyRef = PropertyRef(
        "progress",
        description="Completion percentage of the scan, from 0 to 100.",
    )
    duration: PropertyRef = PropertyRef(
        "duration",
        description="Wall-clock duration of the scan in seconds.",
    )
    provider_id: PropertyRef = PropertyRef(
        "provider_id",
        extra_index=True,
        description="UUID of the Prowler provider that the scan ran against.",
    )
    inserted_at: PropertyRef = PropertyRef(
        "inserted_at",
        description="Timestamp when the scan was created in Prowler.",
    )
    started_at: PropertyRef = PropertyRef(
        "started_at",
        description="Timestamp when the scan began executing.",
    )
    completed_at: PropertyRef = PropertyRef(
        "completed_at",
        description="Timestamp when the scan finished.",
    )
    scheduled_at: PropertyRef = PropertyRef(
        "scheduled_at",
        description="Timestamp the scan was scheduled to start.",
    )
    next_scan_at: PropertyRef = PropertyRef(
        "next_scan_at",
        description="Timestamp of the next scheduled run of this scan.",
    )


@dataclass(frozen=True)
class ProwlerScanToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this ownership relationship.",
    )


@dataclass(frozen=True)
class ProwlerScanToTenantRel(CartographyRelSchema):
    """Links a Prowler tenant to one of its scans."""

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
    properties: ProwlerScanToTenantRelProperties = ProwlerScanToTenantRelProperties()


@dataclass(frozen=True)
class ProwlerScanToProviderRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Prowler last reported this scan target.",
    )


@dataclass(frozen=True)
class ProwlerScanToProviderRel(CartographyRelSchema):
    """Links a Prowler scan to the provider it evaluated."""

    target_node_label: str = "ProwlerProvider"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "provider_id",
                description="UUID of the scanned Prowler provider.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANNED"
    properties: ProwlerScanToProviderRelProperties = (
        ProwlerScanToProviderRelProperties()
    )


@dataclass(frozen=True)
class ProwlerScanSchema(CartographyNodeSchema):
    """A single execution of Prowler's checks against one provider."""

    label: str = "ProwlerScan"
    properties: ProwlerScanNodeProperties = ProwlerScanNodeProperties()
    sub_resource_relationship: ProwlerScanToTenantRel = ProwlerScanToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProwlerScanToProviderRel(),
        ],
    )
