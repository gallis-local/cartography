"""
Data models for Proxmox SDN (Software-Defined Networking) resources.

Follows Cartography's modern data model pattern.
"""

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

# ============================================================================
# ProxmoxSDNZone Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxSDNZoneNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNZone node.

    SDN Zones define virtually separated network areas that can be
    restricted to specific nodes and assigned permissions.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    zone: PropertyRef = PropertyRef("zone", extra_index=True)  # Zone ID/name
    type: PropertyRef = PropertyRef("type")  # simple, vlan, qinq, vxlan, evpn
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # Zone configuration
    bridge: PropertyRef = PropertyRef("bridge")  # Underlying bridge device (e.g., vmbr0)
    nodes: PropertyRef = PropertyRef("nodes")  # Node restrictions (comma-separated)
    mtu: PropertyRef = PropertyRef("mtu")  # MTU size

    # VLAN/VXLAN specific
    tag: PropertyRef = PropertyRef("tag")  # VLAN tag or VXLAN ID

    # VXLAN/EVPN specific
    peers: PropertyRef = PropertyRef("peers")  # Peer addresses (comma-separated)
    controller: PropertyRef = PropertyRef("controller")  # Controller ID (for EVPN)

    # Additional configuration
    ipam: PropertyRef = PropertyRef("ipam")  # IPAM plugin ID
    dns: PropertyRef = PropertyRef("dns")  # DNS plugin ID
    reversedns: PropertyRef = PropertyRef("reversedns")  # Reverse DNS plugin ID
    dnszone: PropertyRef = PropertyRef("dnszone")  # DNS zone name

    # EVPN specific
    vrf_vxlan: PropertyRef = PropertyRef("vrf_vxlan")  # VRF VXLAN ID
    vxlan_port: PropertyRef = PropertyRef("vxlan_port")  # VXLAN UDP port
    mac: PropertyRef = PropertyRef("mac")  # MAC address for VRF

    # QinQ specific
    service_vlan: PropertyRef = PropertyRef("service_vlan")  # Service VLAN (for QinQ)


@dataclass(frozen=True)
class ProxmoxSDNZoneToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSDNZone to ProxmoxCluster.
    """

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
    properties: ProxmoxSDNZoneToClusterRelProperties = ProxmoxSDNZoneToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxSDNZoneSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNZone.

    SDN Zones belong to clusters and contain VNets.
    """

    label: str = "ProxmoxSDNZone"
    properties: ProxmoxSDNZoneNodeProperties = ProxmoxSDNZoneNodeProperties()
    sub_resource_relationship: ProxmoxSDNZoneToClusterRel = ProxmoxSDNZoneToClusterRel()


# ============================================================================
# ProxmoxSDNVNet Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxSDNVNetNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNVNet node.

    VNets (Virtual Networks) belong to zones and become available as
    Linux bridges on nodes for VM/container connectivity.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    vnet: PropertyRef = PropertyRef("vnet", extra_index=True)  # VNet ID/name
    zone: PropertyRef = PropertyRef("zone")  # Parent zone ID
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # VNet configuration
    tag: PropertyRef = PropertyRef("tag")  # VLAN tag (if applicable)
    alias: PropertyRef = PropertyRef("alias")  # Friendly name/description
    vlanaware: PropertyRef = PropertyRef("vlanaware")  # VLAN awareness (0 or 1)

    # Additional configuration
    mac: PropertyRef = PropertyRef("mac")  # MAC address


@dataclass(frozen=True)
class ProxmoxSDNVNetToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSDNVNet to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNVNetToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNVNet)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNVNetToClusterRelProperties = ProxmoxSDNVNetToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxSDNVNetToZoneRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSDNVNet to ProxmoxSDNZone.
    """

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
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxSDNVNetToZoneRel(),
        ]
    )


# ============================================================================
# ProxmoxSDNSubnet Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxSDNSubnetNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNSubnet node.

    Subnets define IP ranges within VNets and handle IPAM/DNS integration.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subnet: PropertyRef = PropertyRef("subnet", extra_index=True)  # CIDR (10.0.1.0/24)
    vnet: PropertyRef = PropertyRef("vnet")  # Parent VNet ID
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # Subnet configuration
    gateway: PropertyRef = PropertyRef("gateway")  # Gateway IP
    snat: PropertyRef = PropertyRef("snat")  # SNAT enabled (0 or 1)

    # DHCP configuration
    dhcp_range: PropertyRef = PropertyRef("dhcp_range")  # DHCP range (start-end IPs)

    # DNS configuration
    dnszoneprefix: PropertyRef = PropertyRef("dnszoneprefix")  # DNS zone prefix


@dataclass(frozen=True)
class ProxmoxSDNSubnetToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSDNSubnet to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNSubnetToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNSubnet)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNSubnetToClusterRelProperties = ProxmoxSDNSubnetToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxSDNSubnetToVNetRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSDNSubnet to ProxmoxSDNVNet.
    """

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
    properties: ProxmoxSDNSubnetToVNetRelProperties = ProxmoxSDNSubnetToVNetRelProperties()


@dataclass(frozen=True)
class ProxmoxSDNSubnetSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNSubnet.

    Subnets belong to VNets and define IP ranges.
    """

    label: str = "ProxmoxSDNSubnet"
    properties: ProxmoxSDNSubnetNodeProperties = ProxmoxSDNSubnetNodeProperties()
    sub_resource_relationship: ProxmoxSDNSubnetToClusterRel = ProxmoxSDNSubnetToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxSDNSubnetToVNetRel(),
        ]
    )


# ============================================================================
# ProxmoxSDNController Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxSDNControllerNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNController node.

    Controllers manage the control plane for zones (e.g., EVPN with BGP).
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    controller: PropertyRef = PropertyRef("controller", extra_index=True)  # Controller ID
    type: PropertyRef = PropertyRef("type")  # evpn, bgp, faucet, etc.
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # BGP/EVPN configuration
    asn: PropertyRef = PropertyRef("asn")  # Autonomous System Number
    peers: PropertyRef = PropertyRef("peers")  # BGP peer IPs (comma-separated)
    node: PropertyRef = PropertyRef("node")  # Node where controller runs

    # Additional EVPN configuration
    ebgp: PropertyRef = PropertyRef("ebgp")  # eBGP mode enabled (0 or 1)
    loopback: PropertyRef = PropertyRef("loopback")  # Loopback IP address
    bgp_multipath_as_path_relax: PropertyRef = PropertyRef("bgp_multipath_as_path_relax")


@dataclass(frozen=True)
class ProxmoxSDNControllerToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSDNController to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNControllerToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNController)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNControllerToClusterRelProperties = ProxmoxSDNControllerToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxSDNControllerSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNController.

    Controllers manage routing protocols for advanced zone types.
    """

    label: str = "ProxmoxSDNController"
    properties: ProxmoxSDNControllerNodeProperties = ProxmoxSDNControllerNodeProperties()
    sub_resource_relationship: ProxmoxSDNControllerToClusterRel = ProxmoxSDNControllerToClusterRel()


# ============================================================================
# ProxmoxSDNIPAM Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxSDNIPAMNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNIPAM node.

    IPAM plugins manage IP address allocation for VMs/containers.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ipam: PropertyRef = PropertyRef("ipam", extra_index=True)  # IPAM ID
    type: PropertyRef = PropertyRef("type")  # pve, netbox, phpipam
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # External IPAM configuration
    url: PropertyRef = PropertyRef("url")  # API URL (for external IPAMs)
    # Token is masked to "configured" in transform to avoid storing raw credentials
    token: PropertyRef = PropertyRef("token")
    section: PropertyRef = PropertyRef("section")  # Section/tenant ID (NetBox/phpIPAM)


@dataclass(frozen=True)
class ProxmoxSDNIPAMToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxSDNIPAM to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNIPAMToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxSDNIPAM)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxSDNIPAMToClusterRelProperties = ProxmoxSDNIPAMToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxSDNIPAMSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxSDNIPAM.

    IPAM plugins manage IP address allocation.
    """

    label: str = "ProxmoxSDNIPAM"
    properties: ProxmoxSDNIPAMNodeProperties = ProxmoxSDNIPAMNodeProperties()
    sub_resource_relationship: ProxmoxSDNIPAMToClusterRel = ProxmoxSDNIPAMToClusterRel()
