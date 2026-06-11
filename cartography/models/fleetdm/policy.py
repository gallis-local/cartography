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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    query: PropertyRef = PropertyRef("query")
    description: PropertyRef = PropertyRef("description")
    resolution: PropertyRef = PropertyRef("resolution")
    platform: PropertyRef = PropertyRef("platform")
    critical: PropertyRef = PropertyRef("critical")
    author_id: PropertyRef = PropertyRef("author_id")
    author_name: PropertyRef = PropertyRef("author_name")
    author_email: PropertyRef = PropertyRef("author_email")
    team_id: PropertyRef = PropertyRef("team_id")
    passing_host_count: PropertyRef = PropertyRef("passing_host_count")
    failing_host_count: PropertyRef = PropertyRef("failing_host_count")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class FleetDMPolicyToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMPolicyToTenantRel(CartographyRelSchema):
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
    label: str = "FleetDMPolicy"
    properties: FleetDMPolicyNodeProperties = FleetDMPolicyNodeProperties()
    sub_resource_relationship: FleetDMPolicyToTenantRel = FleetDMPolicyToTenantRel()
