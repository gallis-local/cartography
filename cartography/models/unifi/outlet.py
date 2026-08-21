from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.unifi.extra_labels import IOT_DEVICE
from cartography.models.unifi.extra_labels import POWER_OUTLET


@dataclass(frozen=True)
class UnifiOutletNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiOutlet."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    name: PropertyRef = PropertyRef("name", description="Name.")
    index: PropertyRef = PropertyRef("index", description="Index.")
    has_relay: PropertyRef = PropertyRef("has_relay", description="Has relay.")
    relay_state: PropertyRef = PropertyRef("relay_state", description="Relay state.")
    cycle_enabled: PropertyRef = PropertyRef(
        "cycle_enabled", description="Cycle enabled."
    )
    has_metering: PropertyRef = PropertyRef("has_metering", description="Has metering.")
    caps: PropertyRef = PropertyRef("caps", description="Caps.")
    voltage: PropertyRef = PropertyRef("voltage", description="Voltage.")
    current: PropertyRef = PropertyRef("current", description="Current.")
    power: PropertyRef = PropertyRef("power", description="Power.")
    power_factor: PropertyRef = PropertyRef("power_factor", description="Power factor.")
    device_mac: PropertyRef = PropertyRef("device_mac", description="Device mac.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiOutletToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiOutletToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiOutlet)
class UnifiOutletToSiteRel(CartographyRelSchema):
    """Relationship: UnifiOutletToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiOutletToSiteRelProperties = UnifiOutletToSiteRelProperties()


@dataclass(frozen=True)
class UnifiOutletToDeviceRelProperties(CartographyRelProperties):
    """Properties of the UnifiOutletToDevice relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiDevice)-[:HAS_OUTLET]->(:UnifiOutlet)
class UnifiOutletToDeviceRel(CartographyRelSchema):
    """Relationship: UnifiOutletToDevice."""

    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_mac")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_OUTLET"
    properties: UnifiOutletToDeviceRelProperties = UnifiOutletToDeviceRelProperties()


@dataclass(frozen=True)
class UnifiOutletSchema(CartographyNodeSchema):
    """A UnifiOutlet."""

    label: str = "UnifiOutlet"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([POWER_OUTLET, IOT_DEVICE])
    properties: UnifiOutletNodeProperties = UnifiOutletNodeProperties()
    sub_resource_relationship: UnifiOutletToSiteRel = UnifiOutletToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiOutletToDeviceRel(),
        ],
    )
