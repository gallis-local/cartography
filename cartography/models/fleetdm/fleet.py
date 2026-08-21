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
class FleetDMFleetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this resource in Fleet."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the resource.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the resource."
    )
    host_count: PropertyRef = PropertyRef(
        "host_count", description="Number of hosts associated with this resource."
    )
    user_count: PropertyRef = PropertyRef(
        "user_count", description="Number of users associated with this resource."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the resource was created in Fleet."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the resource was last updated in Fleet.",
    )


@dataclass(frozen=True)
class FleetDMFleetToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMFleetToTenantRel(CartographyRelSchema):
    target_node_label: str = "FleetDMTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FleetDMFleetToTenantRelProperties = FleetDMFleetToTenantRelProperties()


@dataclass(frozen=True)
class FleetDMFleetSchema(CartographyNodeSchema):
    label: str = "FleetDMFleet"
    properties: FleetDMFleetNodeProperties = FleetDMFleetNodeProperties()
    sub_resource_relationship: FleetDMFleetToTenantRel = FleetDMFleetToTenantRel()
