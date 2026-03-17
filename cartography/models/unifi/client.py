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
class UnifiClientNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("mac")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    is_guest: PropertyRef = PropertyRef("is_guest")
    mac: PropertyRef = PropertyRef("mac")
    ip: PropertyRef = PropertyRef("ip")
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
    sw_mac: PropertyRef = PropertyRef("sw_mac")
    sw_port: PropertyRef = PropertyRef("sw_port")
    ap_switch_mac: PropertyRef = PropertyRef("ap_switch_mac")


@dataclass(frozen=True)
class UnifiClientToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)<-[:RESOURCE]-(:UnifiClient)
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
# (:UnifiDevice)<-[:CONNECTED_TO_AP]-(:UnifiClient)  -- wireless clients only
class UnifiClientToAPRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ap_mac")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONNECTED_TO_AP"
    properties: UnifiClientToAPRelProperties = UnifiClientToAPRelProperties()


@dataclass(frozen=True)
class UnifiClientToSwitchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiDevice)<-[:CONNECTED_TO_SWITCH]-(:UnifiClient)  -- wired clients only
class UnifiClientToSwitchRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("sw_mac")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONNECTED_TO_SWITCH"
    properties: UnifiClientToSwitchRelProperties = UnifiClientToSwitchRelProperties()


@dataclass(frozen=True)
class UnifiClientToAPSwitchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiDevice)<-[:CONNECTED_TO_SWITCH]-(:UnifiClient)  -- wireless clients (via AP uplink switch)
class UnifiClientToAPSwitchRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ap_switch_mac")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONNECTED_TO_SWITCH"
    properties: UnifiClientToAPSwitchRelProperties = UnifiClientToAPSwitchRelProperties()


@dataclass(frozen=True)
class UnifiClientToWlanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiWlan)<-[:CONNECTED_TO_WLAN]-(:UnifiClient)
class UnifiClientToWlanRel(CartographyRelSchema):
    target_node_label: str = "UnifiWlan"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("essid"),
            "site_id": PropertyRef("site_id", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONNECTED_TO_WLAN"
    properties: UnifiClientToWlanRelProperties = UnifiClientToWlanRelProperties()


@dataclass(frozen=True)
class UnifiClientToPortRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiPort)<-[:CONNECTED_VIA]-(:UnifiClient)  -- wired clients only
class UnifiClientToPortRel(CartographyRelSchema):
    target_node_label: str = "UnifiPort"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("port_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONNECTED_VIA"
    properties: UnifiClientToPortRelProperties = UnifiClientToPortRelProperties()


@dataclass(frozen=True)
class UnifiClientSchema(CartographyNodeSchema):
    label: str = "UnifiClient"
    properties: UnifiClientNodeProperties = UnifiClientNodeProperties()
    sub_resource_relationship: UnifiClientToSiteRel = UnifiClientToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiClientToAPRel(),
            UnifiClientToSwitchRel(),
            UnifiClientToAPSwitchRel(),
            UnifiClientToWlanRel(),
            UnifiClientToPortRel(),
        ],
    )
