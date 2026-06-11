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
class FleetDMSoftwareVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    version: PropertyRef = PropertyRef("version")
    source: PropertyRef = PropertyRef("source")
    release: PropertyRef = PropertyRef("release")
    platform: PropertyRef = PropertyRef("platform")
    vendor: PropertyRef = PropertyRef("vendor")
    arch: PropertyRef = PropertyRef("arch")
    generated_cpe: PropertyRef = PropertyRef("generated_cpe")
    hosts_count: PropertyRef = PropertyRef("hosts_count")
    browser: PropertyRef = PropertyRef("browser")
    extension_id: PropertyRef = PropertyRef("extension_id")
    vulnerabilities_count: PropertyRef = PropertyRef("vulnerabilities_count")


@dataclass(frozen=True)
class FleetDMSoftwareVersionToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMSoftwareVersionToTenantRel(CartographyRelSchema):
    target_node_label: str = "FleetDMTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FleetDMSoftwareVersionToTenantRelProperties = (
        FleetDMSoftwareVersionToTenantRelProperties()
    )


@dataclass(frozen=True)
class FleetDMSoftwareVersionSchema(CartographyNodeSchema):
    label: str = "FleetDMSoftwareVersion"
    properties: FleetDMSoftwareVersionNodeProperties = (
        FleetDMSoftwareVersionNodeProperties()
    )
    sub_resource_relationship: FleetDMSoftwareVersionToTenantRel = (
        FleetDMSoftwareVersionToTenantRel()
    )
