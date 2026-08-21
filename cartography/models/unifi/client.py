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
from cartography.models.ontology.labels import USER_ACCOUNT
from cartography.models.unifi.extra_labels import NETWORK_ENDPOINT


@dataclass(frozen=True)
class UnifiClientNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiClient."""

    id: PropertyRef = PropertyRef("mac", description="Mac.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    is_guest: PropertyRef = PropertyRef("is_guest", description="Is guest.")
    mac: PropertyRef = PropertyRef("mac", description="Mac.")
    ip: PropertyRef = PropertyRef("ip", extra_index=True, description="Ip.")
    oui: PropertyRef = PropertyRef("oui", description="Oui.")
    satisfaction: PropertyRef = PropertyRef("satisfaction", description="Satisfaction.")
    channel: PropertyRef = PropertyRef("channel", description="Channel.")
    radio: PropertyRef = PropertyRef("radio", description="Radio.")
    is_wired: PropertyRef = PropertyRef("is_wired", description="Is wired.")
    qos_policy_applied: PropertyRef = PropertyRef(
        "qos_policy_applied", description="Qos policy applied."
    )
    hostname: PropertyRef = PropertyRef("hostname", description="Hostname.")
    name: PropertyRef = PropertyRef("name", description="Name.")
    essid: PropertyRef = PropertyRef("essid", description="Essid.")
    blocked: PropertyRef = PropertyRef("blocked", description="Blocked.")
    uptime: PropertyRef = PropertyRef("uptime", description="Uptime.")
    last_seen: PropertyRef = PropertyRef("last_seen", description="Last seen.")
    vlan: PropertyRef = PropertyRef("vlan", description="Vlan.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )

    # Security-relevant properties
    first_seen: PropertyRef = PropertyRef("first_seen", description="First seen.")
    fixed_ip: PropertyRef = PropertyRef("fixed_ip", description="Fixed ip.")
    idle_time: PropertyRef = PropertyRef("idle_time", description="Idle time.")
    latest_association_time: PropertyRef = PropertyRef(
        "latest_association_time", description="Latest association time."
    )
    rx_bytes: PropertyRef = PropertyRef("rx_bytes", description="Rx bytes.")
    rx_bytes_r: PropertyRef = PropertyRef("rx_bytes_r", description="Rx bytes r.")
    tx_bytes: PropertyRef = PropertyRef("tx_bytes", description="Tx bytes.")
    tx_bytes_r: PropertyRef = PropertyRef("tx_bytes_r", description="Tx bytes r.")
    wired_rx_bytes: PropertyRef = PropertyRef(
        "wired_rx_bytes", description="Wired rx bytes."
    )
    wired_rx_bytes_r: PropertyRef = PropertyRef(
        "wired_rx_bytes_r", description="Wired rx bytes r."
    )
    wired_tx_bytes: PropertyRef = PropertyRef(
        "wired_tx_bytes", description="Wired tx bytes."
    )
    wired_tx_bytes_r: PropertyRef = PropertyRef(
        "wired_tx_bytes_r", description="Wired tx bytes r."
    )
    wired_rate_mbps: PropertyRef = PropertyRef(
        "wired_rate_mbps", description="Wired rate mbps."
    )
    uptime_by_access_point: PropertyRef = PropertyRef(
        "uptime_by_access_point", description="Uptime by access point."
    )
    uptime_by_gateway: PropertyRef = PropertyRef(
        "uptime_by_gateway", description="Uptime by gateway."
    )
    uptime_by_switch: PropertyRef = PropertyRef(
        "uptime_by_switch", description="Uptime by switch."
    )
    switch_depth: PropertyRef = PropertyRef("switch_depth", description="Switch depth.")
    powersave_enabled: PropertyRef = PropertyRef(
        "powersave_enabled", description="Powersave enabled."
    )
    device_name: PropertyRef = PropertyRef("device_name", description="Device name.")
    firmware_version: PropertyRef = PropertyRef(
        "firmware_version", description="Firmware version."
    )
    association_time: PropertyRef = PropertyRef(
        "association_time", description="Association time."
    )
    last_seen_by_access_point: PropertyRef = PropertyRef(
        "last_seen_by_access_point", description="Last seen by access point."
    )
    last_seen_by_gateway: PropertyRef = PropertyRef(
        "last_seen_by_gateway", description="Last seen by gateway."
    )
    last_seen_by_switch: PropertyRef = PropertyRef(
        "last_seen_by_switch", description="Last seen by switch."
    )
    # Historical flag - True for clients from clients_all (historical), False for current clients
    is_historical: PropertyRef = PropertyRef(
        "is_historical", description="Is historical."
    )
    # Network/authentication properties (aiounifi TypedClient: network_id, authorized, gw_mac)
    network_id: PropertyRef = PropertyRef(
        "network_id", extra_index=True, description="Network id."
    )
    authorized: PropertyRef = PropertyRef("authorized", description="Authorized.")
    gw_mac: PropertyRef = PropertyRef("gw_mac", description="Gw mac.")


@dataclass(frozen=True)
class UnifiClientToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiClientToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiClient)
class UnifiClientToSiteRel(CartographyRelSchema):
    """Relationship: UnifiClientToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiClientToSiteRelProperties = UnifiClientToSiteRelProperties()


@dataclass(frozen=True)
class UnifiClientToAPRelProperties(CartographyRelProperties):
    """Properties of the UnifiClientToAP relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_TO_AP]->(:UnifiDevice)  -- wireless clients only
class UnifiClientToAPRel(CartographyRelSchema):
    """Relationship: UnifiClientToAP."""

    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ap_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_AP"
    properties: UnifiClientToAPRelProperties = UnifiClientToAPRelProperties()


@dataclass(frozen=True)
class UnifiClientToSwitchRelProperties(CartographyRelProperties):
    """Properties of the UnifiClientToSwitch relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_TO_SWITCH]->(:UnifiDevice)  -- wired clients only
class UnifiClientToSwitchRel(CartographyRelSchema):
    """Relationship: UnifiClientToSwitch."""

    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("sw_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_SWITCH"
    properties: UnifiClientToSwitchRelProperties = UnifiClientToSwitchRelProperties()


@dataclass(frozen=True)
class UnifiClientToAPSwitchRelProperties(CartographyRelProperties):
    """Properties of the UnifiClientToAPSwitch relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiClient)-[:UPLINKED_TO_SWITCH]->(:UnifiDevice)  -- wireless clients (AP uplinks to this switch)
class UnifiClientToAPSwitchRel(CartographyRelSchema):
    """Relationship: UnifiClientToAPSwitch."""

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
    """Properties of the UnifiClientToWlan relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_TO_WLAN]->(:UnifiWlan)
class UnifiClientToWlanRel(CartographyRelSchema):
    """Relationship: UnifiClientToWlan."""

    target_node_label: str = "UnifiWlan"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("wlanconf_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_WLAN"
    properties: UnifiClientToWlanRelProperties = UnifiClientToWlanRelProperties()


@dataclass(frozen=True)
class UnifiClientToPortRelProperties(CartographyRelProperties):
    """Properties of the UnifiClientToPort relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_VIA]->(:UnifiPort)  -- wired clients only
class UnifiClientToPortRel(CartographyRelSchema):
    """Relationship: UnifiClientToPort."""

    target_node_label: str = "UnifiPort"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("port_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_VIA"
    properties: UnifiClientToPortRelProperties = UnifiClientToPortRelProperties()


@dataclass(frozen=True)
class UnifiClientToGatewayRelProperties(CartographyRelProperties):
    """Properties of the UnifiClientToGateway relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiClient)-[:CONNECTED_TO_GATEWAY]->(:UnifiDevice)  -- via gw_mac (aiounifi TypedClient.gw_mac)
class UnifiClientToGatewayRel(CartographyRelSchema):
    """Relationship: UnifiClientToGateway."""

    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gw_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_GATEWAY"
    properties: UnifiClientToGatewayRelProperties = UnifiClientToGatewayRelProperties()


@dataclass(frozen=True)
class UnifiClientToUserAccountRelProperties(CartographyRelProperties):
    """Properties of the UnifiClientToUserAccount relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiClient)-[:HAS_ACCOUNT]->(:UserAccount) via hostname (best effort)
class UnifiClientToUserAccountRel(CartographyRelSchema):
    """Relationship: UnifiClientToUserAccount."""

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
    """A UnifiClient."""

    label: str = "UnifiClient"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [NETWORK_ENDPOINT, USER_ACCOUNT]
    )
    properties: UnifiClientNodeProperties = UnifiClientNodeProperties()
    sub_resource_relationship: UnifiClientToSiteRel = UnifiClientToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiClientToAPRel(),
            UnifiClientToSwitchRel(),
            UnifiClientToAPSwitchRel(),
            UnifiClientToWlanRel(),
            UnifiClientToPortRel(),
            UnifiClientToGatewayRel(),
            UnifiClientToUserAccountRel(),
        ],
    )
