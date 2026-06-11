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
class UnifiNetworkConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    enabled: PropertyRef = PropertyRef("enabled")
    target_type: PropertyRef = PropertyRef("target_type")
    targets: PropertyRef = PropertyRef("targets", one_to_many=True)
    # Secure configuration (nested dict)
    secure_enabled: PropertyRef = PropertyRef("secure_enabled")
    secure_firewall_rules: PropertyRef = PropertyRef("secure_firewall_rules")
    secure_group_ids: PropertyRef = PropertyRef("secure_group_ids")
    # QoS configuration (nested dict)
    qos_enabled: PropertyRef = PropertyRef("qos_enabled")
    qos_bandwidth_limit: PropertyRef = PropertyRef("qos_bandwidth_limit")
    qos_dscp: PropertyRef = PropertyRef("qos_dscp")
    # Route configuration (nested dict)
    route_enabled: PropertyRef = PropertyRef("route_enabled")
    route_nexthop: PropertyRef = PropertyRef("route_nexthop")
    route_network: PropertyRef = PropertyRef("route_network")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiNetworkConfigToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiNetworkConfig)
class UnifiNetworkConfigToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiNetworkConfigToSiteRelProperties = (
        UnifiNetworkConfigToSiteRelProperties()
    )


@dataclass(frozen=True)
class UnifiNetworkConfigToFirewallZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiNetworkConfig)-[:REFERENCES_ZONE]->(:UnifiFirewallZone)
class UnifiNetworkConfigToFirewallZoneRel(CartographyRelSchema):
    target_node_label: str = "UnifiFirewallZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secure_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES_ZONE"
    properties: UnifiNetworkConfigToFirewallZoneRelProperties = (
        UnifiNetworkConfigToFirewallZoneRelProperties()
    )


@dataclass(frozen=True)
class UnifiNetworkConfigSchema(CartographyNodeSchema):
    label: str = "UnifiNetworkConfig"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["NetworkQoSPolicy", "NetworkSecurityPolicy", "NetworkRoutingPolicy"]
    )
    properties: UnifiNetworkConfigNodeProperties = UnifiNetworkConfigNodeProperties()
    sub_resource_relationship: UnifiNetworkConfigToSiteRel = (
        UnifiNetworkConfigToSiteRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiNetworkConfigToFirewallZoneRel(),
        ],
    )
