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
class UnifiDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("mac")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    mac: PropertyRef = PropertyRef("mac")
    adopted: PropertyRef = PropertyRef("adopted")
    type: PropertyRef = PropertyRef("type")
    model: PropertyRef = PropertyRef("model")
    name: PropertyRef = PropertyRef("name")
    ip: PropertyRef = PropertyRef("ip")
    version: PropertyRef = PropertyRef("version")
    state: PropertyRef = PropertyRef("state")
    uptime: PropertyRef = PropertyRef("uptime")
    last_seen: PropertyRef = PropertyRef("last_seen")
    upgradable: PropertyRef = PropertyRef("upgradable")
    uplink_mac: PropertyRef = PropertyRef("uplink_mac")
    uplink_port_id: PropertyRef = PropertyRef("uplink_port_id")
    wlan_ids: PropertyRef = PropertyRef("wlan_ids")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiDeviceToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiDevice)
class UnifiDeviceToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiDeviceToSiteRelProperties = UnifiDeviceToSiteRelProperties()


@dataclass(frozen=True)
class UnifiDeviceToUplinkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiDevice)-[:UPLINK_TO]->(:UnifiDevice)
class UnifiDeviceToUplinkRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uplink_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "UPLINK_TO"
    properties: UnifiDeviceToUplinkRelProperties = UnifiDeviceToUplinkRelProperties()


@dataclass(frozen=True)
class UnifiDeviceToUplinkPortRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiDevice)-[:UPLINK_VIA_PORT]->(:UnifiPort)
class UnifiDeviceToUplinkPortRel(CartographyRelSchema):
    target_node_label: str = "UnifiPort"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uplink_port_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "UPLINK_VIA_PORT"
    properties: UnifiDeviceToUplinkPortRelProperties = (
        UnifiDeviceToUplinkPortRelProperties()
    )


@dataclass(frozen=True)
class UnifiDeviceBroadcastsWlanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiDevice)-[:BROADCASTS]->(:UnifiWlan)
class UnifiDeviceBroadcastsWlanRel(CartographyRelSchema):
    target_node_label: str = "UnifiWlan"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("wlan_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BROADCASTS"
    properties: UnifiDeviceBroadcastsWlanRelProperties = (
        UnifiDeviceBroadcastsWlanRelProperties()
    )


@dataclass(frozen=True)
class UnifiDeviceSchema(CartographyNodeSchema):
    label: str = "UnifiDevice"
    properties: UnifiDeviceNodeProperties = UnifiDeviceNodeProperties()
    sub_resource_relationship: UnifiDeviceToSiteRel = UnifiDeviceToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiDeviceToUplinkRel(),
            UnifiDeviceToUplinkPortRel(),
            UnifiDeviceBroadcastsWlanRel(),
        ],
    )
