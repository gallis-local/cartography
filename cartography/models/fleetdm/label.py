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
class FleetDMLabelNodeProperties(CartographyNodeProperties):
    """Properties of a FleetDMLabel node (a static or dynamic host grouping)."""

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
    query: PropertyRef = PropertyRef(
        "query", description="Osquery SQL query used to evaluate this resource."
    )
    platform: PropertyRef = PropertyRef(
        "platform", description="Target platform(s) this resource applies to."
    )
    label_type: PropertyRef = PropertyRef(
        "label_type", description="Type of label (e.g. builtin or regular)."
    )
    label_membership_type: PropertyRef = PropertyRef(
        "label_membership_type",
        description="How host membership in this label is determined (dynamic or manual).",
    )
    host_count: PropertyRef = PropertyRef(
        "host_count", description="Number of hosts associated with this resource."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the resource was created in Fleet."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the resource was last updated in Fleet.",
    )


@dataclass(frozen=True)
class FleetDMLabelToTenantRelProperties(CartographyRelProperties):
    """Properties of the FleetDMLabel->FleetDMTenant RESOURCE relationship."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMLabelToTenantRel(CartographyRelSchema):
    """Connects a label to the tenant it belongs to."""

    target_node_label: str = "FleetDMTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FleetDMLabelToTenantRelProperties = FleetDMLabelToTenantRelProperties()


@dataclass(frozen=True)
class FleetDMLabelSchema(CartographyNodeSchema):
    """A Fleet label: a static or dynamic (query-based) grouping of hosts."""

    label: str = "FleetDMLabel"
    properties: FleetDMLabelNodeProperties = FleetDMLabelNodeProperties()
    sub_resource_relationship: FleetDMLabelToTenantRel = FleetDMLabelToTenantRel()
