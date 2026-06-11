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
class FleetDMSoftwareNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    source: PropertyRef = PropertyRef("source")
    browser: PropertyRef = PropertyRef("browser")
    hosts_count: PropertyRef = PropertyRef("hosts_count")
    versions_count: PropertyRef = PropertyRef("versions_count")
    bundle_identifier: PropertyRef = PropertyRef("bundle_identifier")
    display_name: PropertyRef = PropertyRef("display_name")


@dataclass(frozen=True)
class FleetDMSoftwareToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMSoftwareToTenantRel(CartographyRelSchema):
    target_node_label: str = "FleetDMTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FleetDMSoftwareToTenantRelProperties = (
        FleetDMSoftwareToTenantRelProperties()
    )


@dataclass(frozen=True)
class FleetDMSoftwareSchema(CartographyNodeSchema):
    label: str = "FleetDMSoftware"
    properties: FleetDMSoftwareNodeProperties = FleetDMSoftwareNodeProperties()
    sub_resource_relationship: FleetDMSoftwareToTenantRel = FleetDMSoftwareToTenantRel()
