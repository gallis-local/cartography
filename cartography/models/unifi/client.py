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
class UnifiClientNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("mac")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    is_guest: PropertyRef = PropertyRef("is_guest")
    mac: PropertyRef = PropertyRef("mac")
    ip: PropertyRef = PropertyRef("ip", extra_index=True)
    oui: PropertyRef = PropertyRef("oui")
    satisfaction: PropertyRef = PropertyRef("satisfaction")
    channel: PropertyRef = PropertyRef("channel")
    radio: PropertyRef = PropertyRef("radio")
    is_wired: PropertyRef = PropertyRef("is_wired")
    qos_policy_applied: PropertyRef = PropertyRef("qos_policy_applied")
    hostname: PropertyRef = PropertyRef("hostname")
    name: PropertyRef = PropertyRef("name")
    essid: PropertyRef = PropertyRef("essid")
    blocked: PropertyRef = PropertyRef("blocked")
    uptime: PropertyRef = PropertyRef("uptime")
    last_seen: PropertyRef = PropertyRef("last_seen")
    vlan: PropertyRef = PropertyRef("vlan")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)

    # Security-relevant properties
    first_seen: PropertyRef = PropertyRef("first_seen")
    fixed_ip: PropertyRef = PropertyRef("fixed_ip")
    idle_time: PropertyRef = PropertyRef("idle_time")
    latest_association_time: PropertyRef = PropertyRef("latest_association_time")
    rx_bytes: PropertyRef = PropertyRef("rx_bytes")
    rx_bytes_r: PropertyRef = PropertyRef("rx_bytes_r")
    tx_bytes: PropertyRef = PropertyRef("tx_bytes")
    tx_bytes_r: PropertyRef = PropertyRef("tx_bytes_r")
    wired_rx_bytes: PropertyRef = PropertyRef("wired_rx_bytes")
    wired_rx_bytes_r: PropertyRef = PropertyRef("wired_rx_bytes_r")
    wired_tx_bytes: PropertyRef = PropertyRef("wired_tx_bytes")
    wired_tx_bytes_r: PropertyRef = PropertyRef("wired_tx_bytes_r")
    wired_rate_mbps: PropertyRef = PropertyRef("wired_rate_mbps")
    uptime_by_access_point: PropertyRef = PropertyRef("uptime_by_access_point")
    uptime_by_gateway: PropertyRef = PropertyRef("uptime_by_gateway")
    uptime_by_switch: PropertyRef = PropertyRef("uptime_by_switch")
    switch_depth: PropertyRef = PropertyRef("switch_depth")
    powersave_enabled: PropertyRef = PropertyRef("powersave_enabled")
    device_name: PropertyRef = PropertyRef("device_name")
    firmware_version: PropertyRef = PropertyRef("firmware_version")
    association_time: PropertyRef = PropertyRef("association_time")
    last_seen_by_access_point: PropertyRef = PropertyRef("last_seen_by_access_point")
    last_seen_by_gateway: PropertyRef = PropertyRef("last_seen_by_gateway")
    last_seen_by_switch: PropertyRef = PropertyRef("last_seen_by_switch")
    # Historical flag - True for clients from clients_all (historical), False for current clients
    is_historical: PropertyRef = PropertyRef("is_historical")


@dataclass(frozen=True)
class UnifiClientToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiClient)
class UnifiClientToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiClientToSiteRelProperties = UnifiClientToSiteRelProperties()


@dataclass(frozen=True)
class UnifiClientToAPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_TO_AP]->(:UnifiDevice)  -- wireless clients only
class UnifiClientToAPRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ap_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_AP"
    properties: UnifiClientToAPRelProperties = UnifiClientToAPRelProperties()


@dataclass(frozen=True)
class UnifiClientToSwitchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_TO_SWITCH]->(:UnifiDevice)  -- wired clients only
class UnifiClientToSwitchRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("sw_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_SWITCH"
    properties: UnifiClientToSwitchRelProperties = UnifiClientToSwitchRelProperties()


@dataclass(frozen=True)
class UnifiClientToAPSwitchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiClient)-[:UPLINKED_TO_SWITCH]->(:UnifiDevice)  -- wireless clients (AP uplinks to this switch)
class UnifiClientToAPSwitchRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ap_switch_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "UPLINKED_TO_SWITCH"
    properties: UnifiClientToAPSwitchRelProperties = (
        UnifiClientToAPSwitchRelProperties()
    )


@dataclass(frozen=True)
class UnifiClientToWlanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_TO_WLAN]->(:UnifiWlan)
class UnifiClientToWlanRel(CartographyRelSchema):
    target_node_label: str = "UnifiWlan"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("wlanconf_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_WLAN"
    properties: UnifiClientToWlanRelProperties = UnifiClientToWlanRelProperties()


@dataclass(frozen=True)
class UnifiClientToPortRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_VIA]->(:UnifiPort)  -- wired clients only
class UnifiClientToPortRel(CartographyRelSchema):
    target_node_label: str = "UnifiPort"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("port_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_VIA"
    properties: UnifiClientToPortRelProperties = UnifiClientToPortRelProperties()


@dataclass(frozen=True)
class UnifiClientToUserAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiClient)-[:HAS_ACCOUNT]->(:UserAccount) via hostname (best effort)
class UnifiClientToUserAccountRel(CartographyRelSchema):
    target_node_label: str = "UserAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCOUNT"
    properties: UnifiClientToUserAccountRelProperties = (
        UnifiClientToUserAccountRelProperties()
    )


@dataclass(frozen=True)
class UnifiClientSchema(CartographyNodeSchema):
    label: str = "UnifiClient"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NetworkEndpoint"])
    properties: UnifiClientNodeProperties = UnifiClientNodeProperties()
    sub_resource_relationship: UnifiClientToSiteRel = UnifiClientToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiClientToAPRel(),
            UnifiClientToSwitchRel(),
            UnifiClientToAPSwitchRel(),
            UnifiClientToWlanRel(),
            UnifiClientToPortRel(),
            UnifiClientToUserAccountRel(),
        ],
    )
