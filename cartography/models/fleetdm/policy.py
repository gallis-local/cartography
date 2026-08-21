from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class FleetDMPolicyNodeProperties(CartographyNodeProperties):
    """Properties of a FleetDMPolicy node (an osquery-based compliance check)."""

    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this resource in Fleet."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the resource.",
    )
    query: PropertyRef = PropertyRef(
        "query", description="Osquery SQL query used to evaluate this resource."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the resource."
    )
    resolution: PropertyRef = PropertyRef(
        "resolution", description="Guidance on how to resolve a failing policy."
    )
    platform: PropertyRef = PropertyRef(
        "platform", description="Target platform(s) this resource applies to."
    )
    critical: PropertyRef = PropertyRef(
        "critical", description="Whether this policy is marked as critical."
    )
    author_id: PropertyRef = PropertyRef(
        "author_id", description="Fleet user ID of the policy's author."
    )
    author_name: PropertyRef = PropertyRef(
        "author_name", description="Name of the policy's author."
    )
    author_email: PropertyRef = PropertyRef(
        "author_email", description="Email of the policy's author."
    )
    team_id: PropertyRef = PropertyRef(
        "team_id", description="ID of the Fleet team this policy belongs to."
    )
    passing_host_count: PropertyRef = PropertyRef(
        "passing_host_count",
        description="Number of hosts currently passing this policy.",
    )
    failing_host_count: PropertyRef = PropertyRef(
        "failing_host_count",
        description="Number of hosts currently failing this policy.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the resource was created in Fleet."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the resource was last updated in Fleet.",
    )


@dataclass(frozen=True)
class FleetDMPolicyToTenantRelProperties(CartographyRelProperties):
    """Properties of the FleetDMPolicy->FleetDMTenant RESOURCE relationship."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMPolicyToTenantRel(CartographyRelSchema):
    """Connects a policy to the tenant it belongs to."""

    target_node_label: str = "FleetDMTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FleetDMPolicyToTenantRelProperties = (
        FleetDMPolicyToTenantRelProperties()
    )


@dataclass(frozen=True)
class FleetDMPolicySchema(CartographyNodeSchema):
    """An osquery-based compliance policy that hosts are checked against."""

    label: str = "FleetDMPolicy"
    properties: FleetDMPolicyNodeProperties = FleetDMPolicyNodeProperties()
    sub_resource_relationship: FleetDMPolicyToTenantRel = FleetDMPolicyToTenantRel()
