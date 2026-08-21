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
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this resource in Fleet."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the resource.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="Origin of the software inventory entry (e.g. apps, programs, deb_packages).",
    )
    browser: PropertyRef = PropertyRef(
        "browser",
        description="Browser the software extension/plugin belongs to, if applicable.",
    )
    hosts_count: PropertyRef = PropertyRef(
        "hosts_count", description="Number of hosts with this software installed."
    )
    versions_count: PropertyRef = PropertyRef(
        "versions_count",
        description="Number of distinct versions of this software title observed.",
    )
    bundle_identifier: PropertyRef = PropertyRef(
        "bundle_identifier", description="macOS bundle identifier for the software."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Human-readable display name."
    )


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
