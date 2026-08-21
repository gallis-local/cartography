from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.unifi.extra_labels import NETWORK_CONTROLLER


@dataclass(frozen=True)
class UnifiSystemInfoNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiSystemInfo."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    anonymous_controller_id: PropertyRef = PropertyRef(
        "anonymous_controller_id", extra_index=True
    )
    hostname: PropertyRef = PropertyRef("hostname", description="Hostname.")
    name: PropertyRef = PropertyRef("name", description="Name.")
    version: PropertyRef = PropertyRef("version", description="Version.")
    previous_version: PropertyRef = PropertyRef(
        "previous_version", description="Previous version."
    )
    update_available: PropertyRef = PropertyRef(
        "update_available", description="Update available."
    )
    ip_addrs: PropertyRef = PropertyRef("ip_addrs", description="Ip addrs.")
    is_cloud_console: PropertyRef = PropertyRef(
        "is_cloud_console", description="Is cloud console."
    )
    ubnt_device_type: PropertyRef = PropertyRef(
        "ubnt_device_type", description="Ubnt device type."
    )
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiSystemInfoToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiSystemInfoToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiSystemInfo)
class UnifiSystemInfoToSiteRel(CartographyRelSchema):
    """Relationship: UnifiSystemInfoToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiSystemInfoToSiteRelProperties = (
        UnifiSystemInfoToSiteRelProperties()
    )


@dataclass(frozen=True)
class UnifiSystemInfoSchema(CartographyNodeSchema):
    """A UnifiSystemInfo."""

    label: str = "UnifiSystemInfo"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_CONTROLLER])
    properties: UnifiSystemInfoNodeProperties = UnifiSystemInfoNodeProperties()
    sub_resource_relationship: UnifiSystemInfoToSiteRel = UnifiSystemInfoToSiteRel()
