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
from cartography.models.unifi.extra_labels import NETWORK_INTERFACE


@dataclass(frozen=True)
class UnifiNetworkConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    enabled: PropertyRef = PropertyRef("enabled")
    purpose: PropertyRef = PropertyRef(
        "purpose",
        description='Role of the network, e.g. "corporate", "guest", "wan", "vlan-only".',
    )
    networkgroup: PropertyRef = PropertyRef(
        "networkgroup", description="Interface group the network is attached to."
    )
    domain_name: PropertyRef = PropertyRef(
        "domain_name", description="DNS domain name advertised to clients."
    )
    vlan_enabled: PropertyRef = PropertyRef(
        "vlan_enabled", description="Whether this network is tagged to a VLAN."
    )
    vlan: PropertyRef = PropertyRef("vlan", description="VLAN ID, if tagged.")
    ip_subnet: PropertyRef = PropertyRef(
        "ip_subnet", description="Gateway IP and subnet mask for this network."
    )
    is_guest: PropertyRef = PropertyRef(
        "is_guest", description="Whether this is a guest network."
    )
    is_nat: PropertyRef = PropertyRef(
        "is_nat", description="Whether traffic from this network is NAT'd."
    )
    attr_no_delete: PropertyRef = PropertyRef(
        "attr_no_delete",
        description="Whether this is a built-in network that cannot be deleted.",
    )
    dhcpd_enabled: PropertyRef = PropertyRef(
        "dhcpd_enabled", description="Whether the DHCP server is enabled."
    )
    dhcpd_start: PropertyRef = PropertyRef(
        "dhcpd_start", description="Start of the DHCP address pool."
    )
    dhcpd_stop: PropertyRef = PropertyRef(
        "dhcpd_stop", description="End of the DHCP address pool."
    )
    dhcpd_leasetime: PropertyRef = PropertyRef(
        "dhcpd_leasetime", description="DHCP lease time, in seconds."
    )
    dhcpd_dns_enabled: PropertyRef = PropertyRef(
        "dhcpd_dns_enabled",
        description="Whether a custom DNS server is pushed to DHCP clients.",
    )
    dhcpd_dns_1: PropertyRef = PropertyRef(
        "dhcpd_dns_1", description="Primary DNS server pushed to DHCP clients."
    )
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
class UnifiNetworkConfigSchema(CartographyNodeSchema):
    label: str = "UnifiNetworkConfig"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_INTERFACE])
    properties: UnifiNetworkConfigNodeProperties = UnifiNetworkConfigNodeProperties()
    sub_resource_relationship: UnifiNetworkConfigToSiteRel = (
        UnifiNetworkConfigToSiteRel()
    )
