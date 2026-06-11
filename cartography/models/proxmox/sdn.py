"""
Data models for Proxmox SDN (Software-Defined Networking) resources.

Follows Cartography's modern data model pattern.
"""

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

# ProxmoxSDNZone Node Schema


@dataclass(frozen=True)
class ProxmoxSDNZoneNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNZone node.

    SDN Zones define virtually separated network areas that can be
    restricted to specific nodes and assigned permissions.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    zone: PropertyRef = PropertyRef("zone", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # Zone configuration
    bridge: PropertyRef = PropertyRef("bridge")
    nodes: PropertyRef = PropertyRef("nodes")
    mtu: PropertyRef = PropertyRef("mtu")

    # VLAN/VXLAN specific
    tag: PropertyRef = PropertyRef("tag")

    # VXLAN/EVPN specific
    peers: PropertyRef = PropertyRef("peers")
    controller: PropertyRef = PropertyRef("controller")

    # Additional configuration
    ipam: PropertyRef = PropertyRef("ipam")
    dns: PropertyRef = PropertyRef("dns")
    reversedns: PropertyRef = PropertyRef("reversedns")
    dnszone: PropertyRef = PropertyRef("dnszone")

    # EVPN specific
    vrf_vxlan: PropertyRef = PropertyRef("vrf_vxlan")
    vxlan_port: PropertyRef = PropertyRef("vxlan_port")
    mac: PropertyRef = PropertyRef("mac")

    # QinQ specific
    service_vlan: PropertyRef = PropertyRef("service_vlan")


@dataclass(frozen=True)
class ProxmoxSDNZoneToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNZoneToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNZone)

    SDN Zones are cluster-wide resources.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNZoneToClusterRelProperties = (
        ProxmoxSDNZoneToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxSDNZoneSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNZone.

    SDN Zones belong to clusters and contain VNets.
    """

    label: str = "ProxmoxSDNZone"
    properties: ProxmoxSDNZoneNodeProperties = ProxmoxSDNZoneNodeProperties()
    sub_resource_relationship: ProxmoxSDNZoneToClusterRel = ProxmoxSDNZoneToClusterRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["VirtualNetwork"])


# ProxmoxSDNVNet Node Schema


@dataclass(frozen=True)
class ProxmoxSDNVNetNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNVNet node.

    VNets (Virtual Networks) belong to zones and become available as
    Linux bridges on nodes for VM/container connectivity.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    vnet: PropertyRef = PropertyRef("vnet", extra_index=True)
    zone: PropertyRef = PropertyRef("zone")
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # VNet configuration
    tag: PropertyRef = PropertyRef("tag")
    alias: PropertyRef = PropertyRef("alias")
    vlanaware: PropertyRef = PropertyRef("vlanaware")

    # Additional configuration
    mac: PropertyRef = PropertyRef("mac")


@dataclass(frozen=True)
class ProxmoxSDNVNetToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNVNet)
class ProxmoxSDNVNetToClusterRel(CartographyRelSchema):
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNVNetToClusterRelProperties = (
        ProxmoxSDNVNetToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxSDNVNetToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNVNetToZoneRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxSDNVNet)-[:BELONGS_TO]->(:ProxmoxSDNZone)

    VNets belong to SDN Zones.
    """

    target_node_label: str = "ProxmoxSDNZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "zone": PropertyRef("zone"),
            "cluster_id": PropertyRef("cluster_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: ProxmoxSDNVNetToZoneRelProperties = ProxmoxSDNVNetToZoneRelProperties()


@dataclass(frozen=True)
class ProxmoxSDNVNetSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNVNet.

    VNets belong to zones and are used by VMs/containers.
    """

    label: str = "ProxmoxSDNVNet"
    properties: ProxmoxSDNVNetNodeProperties = ProxmoxSDNVNetNodeProperties()
    sub_resource_relationship: ProxmoxSDNVNetToClusterRel = ProxmoxSDNVNetToClusterRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Subnet"])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxSDNVNetToZoneRel(),
        ]
    )


# ProxmoxSDNSubnet Node Schema


@dataclass(frozen=True)
class ProxmoxSDNSubnetNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNSubnet node.

    Subnets define IP ranges within VNets and handle IPAM/DNS integration.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subnet: PropertyRef = PropertyRef("subnet", extra_index=True)
    vnet: PropertyRef = PropertyRef("vnet")
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # Subnet configuration
    gateway: PropertyRef = PropertyRef("gateway")
    snat: PropertyRef = PropertyRef("snat")

    # DHCP configuration
    dhcp_range: PropertyRef = PropertyRef("dhcp_range")

    # DNS configuration
    dnszoneprefix: PropertyRef = PropertyRef("dnszoneprefix")


@dataclass(frozen=True)
class ProxmoxSDNSubnetToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNSubnet)
class ProxmoxSDNSubnetToClusterRel(CartographyRelSchema):
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNSubnetToClusterRelProperties = (
        ProxmoxSDNSubnetToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxSDNSubnetToVNetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNSubnetToVNetRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxSDNSubnet)-[:BELONGS_TO]->(:ProxmoxSDNVNet)

    Subnets belong to VNets.
    """

    target_node_label: str = "ProxmoxSDNVNet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vnet": PropertyRef("vnet"),
            "cluster_id": PropertyRef("cluster_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: ProxmoxSDNSubnetToVNetRelProperties = (
        ProxmoxSDNSubnetToVNetRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxSDNSubnetSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNSubnet.

    Subnets belong to VNets and define IP ranges.
    """

    label: str = "ProxmoxSDNSubnet"
    properties: ProxmoxSDNSubnetNodeProperties = ProxmoxSDNSubnetNodeProperties()
    sub_resource_relationship: ProxmoxSDNSubnetToClusterRel = (
        ProxmoxSDNSubnetToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxSDNSubnetToVNetRel(),
        ]
    )


# ProxmoxSDNController Node Schema


@dataclass(frozen=True)
class ProxmoxSDNControllerNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNController node.

    Controllers manage the control plane for zones (e.g., EVPN with BGP).
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    controller: PropertyRef = PropertyRef("controller", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # BGP/EVPN configuration
    asn: PropertyRef = PropertyRef("asn")
    peers: PropertyRef = PropertyRef("peers")
    node: PropertyRef = PropertyRef("node")

    # Additional EVPN configuration
    ebgp: PropertyRef = PropertyRef("ebgp")
    loopback: PropertyRef = PropertyRef("loopback")
    bgp_multipath_as_path_relax: PropertyRef = PropertyRef(
        "bgp_multipath_as_path_relax"
    )


@dataclass(frozen=True)
class ProxmoxSDNControllerToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNController)
class ProxmoxSDNControllerToClusterRel(CartographyRelSchema):
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNControllerToClusterRelProperties = (
        ProxmoxSDNControllerToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxSDNControllerSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNController.

    Controllers manage routing protocols for advanced zone types.
    """

    label: str = "ProxmoxSDNController"
    properties: ProxmoxSDNControllerNodeProperties = (
        ProxmoxSDNControllerNodeProperties()
    )
    sub_resource_relationship: ProxmoxSDNControllerToClusterRel = (
        ProxmoxSDNControllerToClusterRel()
    )


# ProxmoxSDNIPAM Node Schema


@dataclass(frozen=True)
class ProxmoxSDNIPAMNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNIPAM node.

    IPAM plugins manage IP address allocation for VMs/containers.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ipam: PropertyRef = PropertyRef("ipam", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # External IPAM configuration
    url: PropertyRef = PropertyRef("url")
    # Token is masked to "configured" in transform to avoid storing raw credentials
    token: PropertyRef = PropertyRef("token")
    section: PropertyRef = PropertyRef("section")


@dataclass(frozen=True)
class ProxmoxSDNIPAMToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNIPAM)
class ProxmoxSDNIPAMToClusterRel(CartographyRelSchema):
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNIPAMToClusterRelProperties = (
        ProxmoxSDNIPAMToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxSDNIPAMSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNIPAM.

    IPAM plugins manage IP address allocation.
    """

    label: str = "ProxmoxSDNIPAM"
    properties: ProxmoxSDNIPAMNodeProperties = ProxmoxSDNIPAMNodeProperties()
    sub_resource_relationship: ProxmoxSDNIPAMToClusterRel = ProxmoxSDNIPAMToClusterRel()
