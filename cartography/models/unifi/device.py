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
from cartography.models.unifi.extra_labels import NETWORK_INFRASTRUCTURE_DEVICE


@dataclass(frozen=True)
class UnifiDeviceNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiDevice."""

    id: PropertyRef = PropertyRef("mac", description="Mac.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    mac: PropertyRef = PropertyRef("mac", description="Mac.")
    adopted: PropertyRef = PropertyRef("adopted", description="Adopted.")
    type: PropertyRef = PropertyRef("type", description="Type.")
    model: PropertyRef = PropertyRef("model", description="Model.")
    name: PropertyRef = PropertyRef("name", description="Name.")
    ip: PropertyRef = PropertyRef("ip", extra_index=True, description="Ip.")
    version: PropertyRef = PropertyRef("version", description="Version.")
    state: PropertyRef = PropertyRef("state", description="State.")
    uptime: PropertyRef = PropertyRef("uptime", description="Uptime.")
    last_seen: PropertyRef = PropertyRef("last_seen", description="Last seen.")
    upgradable: PropertyRef = PropertyRef("upgradable", description="Upgradable.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )

    # Security-relevant properties
    last_wan_ip: PropertyRef = PropertyRef(
        "last_wan_ip", extra_index=True, description="Last wan ip."
    )
    uplink_depth: PropertyRef = PropertyRef("uplink_depth", description="Uplink depth.")
    user_num_sta: PropertyRef = PropertyRef("user_num_sta", description="User num sta.")
    overheating: PropertyRef = PropertyRef("overheating", description="Overheating.")
    upgrade_to_firmware: PropertyRef = PropertyRef(
        "upgrade_to_firmware", description="Upgrade to firmware."
    )
    outlet_ac_power_budget: PropertyRef = PropertyRef(
        "outlet_ac_power_budget", description="Outlet ac power budget."
    )
    outlet_ac_power_consumption: PropertyRef = PropertyRef(
        "outlet_ac_power_consumption"
    )


@dataclass(frozen=True)
class UnifiDeviceToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiDeviceToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiDevice)
class UnifiDeviceToSiteRel(CartographyRelSchema):
    """Relationship: UnifiDeviceToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiDeviceToSiteRelProperties = UnifiDeviceToSiteRelProperties()


@dataclass(frozen=True)
class UnifiDeviceToUplinkRelProperties(CartographyRelProperties):
    """Properties of the UnifiDeviceToUplink relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiDevice)-[:UPLINK_TO]->(:UnifiDevice)
class UnifiDeviceToUplinkRel(CartographyRelSchema):
    """Relationship: UnifiDeviceToUplink."""

    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uplink_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "UPLINK_TO"
    properties: UnifiDeviceToUplinkRelProperties = UnifiDeviceToUplinkRelProperties()


@dataclass(frozen=True)
class UnifiDeviceToUplinkPortRelProperties(CartographyRelProperties):
    """Properties of the UnifiDeviceToUplinkPort relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiDevice)-[:UPLINK_VIA_PORT]->(:UnifiPort)
class UnifiDeviceToUplinkPortRel(CartographyRelSchema):
    """Relationship: UnifiDeviceToUplinkPort."""

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
    """Properties of the UnifiDeviceBroadcastsWlan relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiDevice)-[:BROADCASTS]->(:UnifiWlan)
class UnifiDeviceBroadcastsWlanRel(CartographyRelSchema):
    """Relationship: UnifiDeviceBroadcastsWlan."""

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
class UnifiDeviceToOntologyDeviceRelProperties(CartographyRelProperties):
    """Properties of the UnifiDeviceToOntologyDevice relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiDevice)-[:OBSERVED_AS]->(:Device) via hostname
class UnifiDeviceToOntologyDeviceRel(CartographyRelSchema):
    """Relationship: UnifiDeviceToOntologyDevice."""

    target_node_label: str = "Device"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_AS"
    properties: UnifiDeviceToOntologyDeviceRelProperties = (
        UnifiDeviceToOntologyDeviceRelProperties()
    )


@dataclass(frozen=True)
class UnifiDeviceSchema(CartographyNodeSchema):
    """A UnifiDevice."""

    label: str = "UnifiDevice"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [NETWORK_INFRASTRUCTURE_DEVICE]
    )
    properties: UnifiDeviceNodeProperties = UnifiDeviceNodeProperties()
    sub_resource_relationship: UnifiDeviceToSiteRel = UnifiDeviceToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiDeviceToUplinkRel(),
            UnifiDeviceToUplinkPortRel(),
            UnifiDeviceBroadcastsWlanRel(),
            UnifiDeviceToOntologyDeviceRel(),
        ],
    )
