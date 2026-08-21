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
    """Properties of a FleetDMSoftwareVersion node (one specific version of a software title)."""

    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this resource in Fleet."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the resource.",
    )
    version: PropertyRef = PropertyRef(
        "version", description="Version string of the software."
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="Origin of the software inventory entry (e.g. apps, programs, deb_packages).",
    )
    release: PropertyRef = PropertyRef(
        "release", description="OS distribution release the package was built for."
    )
    platform: PropertyRef = PropertyRef(
        "platform", description="Target platform(s) this resource applies to."
    )
    vendor: PropertyRef = PropertyRef(
        "vendor", description="Vendor or publisher of the software."
    )
    arch: PropertyRef = PropertyRef(
        "arch", description="CPU architecture the software was built for."
    )
    generated_cpe: PropertyRef = PropertyRef(
        "generated_cpe",
        description="Common Platform Enumeration (CPE) string generated for this software version.",
    )
    hosts_count: PropertyRef = PropertyRef(
        "hosts_count", description="Number of hosts with this software installed."
    )
    browser: PropertyRef = PropertyRef(
        "browser",
        description="Browser the software extension/plugin belongs to, if applicable.",
    )
    extension_id: PropertyRef = PropertyRef(
        "extension_id", description="Browser extension identifier, if applicable."
    )
    vulnerabilities_count: PropertyRef = PropertyRef(
        "vulnerabilities_count",
        description="Number of known vulnerabilities affecting this software version.",
    )


@dataclass(frozen=True)
class FleetDMSoftwareVersionToTenantRelProperties(CartographyRelProperties):
    """Properties of the FleetDMSoftwareVersion->FleetDMTenant RESOURCE relationship."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMSoftwareVersionToTenantRel(CartographyRelSchema):
    """Connects a software version to the tenant it belongs to."""

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
    """A specific version of a software title observed on one or more hosts."""

    label: str = "FleetDMSoftwareVersion"
    properties: FleetDMSoftwareVersionNodeProperties = (
        FleetDMSoftwareVersionNodeProperties()
    )
    sub_resource_relationship: FleetDMSoftwareVersionToTenantRel = (
        FleetDMSoftwareVersionToTenantRel()
    )
