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


@dataclass(frozen=True)
class UnifiOutletNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    index: PropertyRef = PropertyRef("index")
    has_relay: PropertyRef = PropertyRef("has_relay")
    relay_state: PropertyRef = PropertyRef("relay_state")
    cycle_enabled: PropertyRef = PropertyRef("cycle_enabled")
    has_metering: PropertyRef = PropertyRef("has_metering")
    caps: PropertyRef = PropertyRef("caps")
    voltage: PropertyRef = PropertyRef("voltage")
    current: PropertyRef = PropertyRef("current")
    power: PropertyRef = PropertyRef("power")
    power_factor: PropertyRef = PropertyRef("power_factor")
    device_mac: PropertyRef = PropertyRef("device_mac")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiOutletToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiOutlet)
class UnifiOutletToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiOutletToSiteRelProperties = UnifiOutletToSiteRelProperties()


@dataclass(frozen=True)
class UnifiOutletToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiDevice)-[:HAS_OUTLET]->(:UnifiOutlet)
class UnifiOutletToDeviceRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_mac")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_OUTLET"
    properties: UnifiOutletToDeviceRelProperties = UnifiOutletToDeviceRelProperties()


@dataclass(frozen=True)
class UnifiOutletSchema(CartographyNodeSchema):
    label: str = "UnifiOutlet"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PowerOutlet", "IoTDevice"])
    properties: UnifiOutletNodeProperties = UnifiOutletNodeProperties()
    sub_resource_relationship: UnifiOutletToSiteRel = UnifiOutletToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiOutletToDeviceRel(),
        ],
    )
