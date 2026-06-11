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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    query: PropertyRef = PropertyRef("query")
    platform: PropertyRef = PropertyRef("platform")
    label_type: PropertyRef = PropertyRef("label_type")
    label_membership_type: PropertyRef = PropertyRef("label_membership_type")
    host_count: PropertyRef = PropertyRef("host_count")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class FleetDMLabelToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMLabelToTenantRel(CartographyRelSchema):
    target_node_label: str = "FleetDMTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FleetDMLabelToTenantRelProperties = FleetDMLabelToTenantRelProperties()


@dataclass(frozen=True)
class FleetDMLabelSchema(CartographyNodeSchema):
    label: str = "FleetDMLabel"
    properties: FleetDMLabelNodeProperties = FleetDMLabelNodeProperties()
    sub_resource_relationship: FleetDMLabelToTenantRel = FleetDMLabelToTenantRel()
