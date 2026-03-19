from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class UnifiPortNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    port_idx: PropertyRef = PropertyRef("port_idx")
    name: PropertyRef = PropertyRef("name")
    port_poe: PropertyRef = PropertyRef("port_poe")
    poe_enable: PropertyRef = PropertyRef("poe_enable")
    poe_mode: PropertyRef = PropertyRef("poe_mode")
    poe_voltage: PropertyRef = PropertyRef("poe_voltage")
    portconf_id: PropertyRef = PropertyRef("portconf_id")
    up: PropertyRef = PropertyRef("up")
    speed: PropertyRef = PropertyRef("speed")
    full_duplex: PropertyRef = PropertyRef("full_duplex")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiPortToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiPort)
class UnifiPortToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiPortToSiteRelProperties = UnifiPortToSiteRelProperties()


@dataclass(frozen=True)
class UnifiPortToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiDevice)-[:HAS_PORT]->(:UnifiPort)
class UnifiPortToDeviceRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_mac")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PORT"
    properties: UnifiPortToDeviceRelProperties = UnifiPortToDeviceRelProperties()


@dataclass(frozen=True)
class UnifiPortSchema(CartographyNodeSchema):
    label: str = "UnifiPort"
    properties: UnifiPortNodeProperties = UnifiPortNodeProperties()
    sub_resource_relationship: UnifiPortToSiteRel = UnifiPortToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiPortToDeviceRel(),
        ],
    )
