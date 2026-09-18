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
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SUBNET
from cartography.models.ontology.labels import VIRTUAL_NETWORK

# ProxmoxSDNZone Node Schema


@dataclass(frozen=True)
class ProxmoxSDNZoneNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNZone node.

    SDN Zones define virtually separated network areas that can be
    restricted to specific nodes and assigned permissions.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this zone, in the form `{cluster_id}/sdn/zone/{zone}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    zone: PropertyRef = PropertyRef(
        "zone",
        extra_index=True,
        description="SDN zone name, at most 8 characters, used as the zone id under /cluster/sdn/zones.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Zone type, which decides the underlying transport: `simple`, `vlan`, `qinq`, `vxlan` or `evpn`.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )

    # Zone configuration
    bridge: PropertyRef = PropertyRef(
        "bridge",
        description="Host bridge the zone's VNets are built on. Used by `vlan` and `qinq` zones.",
    )
    nodes: PropertyRef = PropertyRef(
        "nodes",
        description="Comma-separated node names the zone is deployed to. Null when it applies to every node.",
    )
    mtu: PropertyRef = PropertyRef(
        "mtu",
        description="MTU in bytes for the zone's interfaces. Encapsulating zone types need it lowered to leave room for their headers.",
    )

    # VLAN/VXLAN specific
    tag: PropertyRef = PropertyRef(
        "tag", description="Outer VLAN tag a `qinq` zone wraps its VNets in."
    )

    # VXLAN/EVPN specific
    peers: PropertyRef = PropertyRef(
        "peers",
        description="Comma-separated addresses of the other nodes taking part in a `vxlan` zone's unicast mesh.",
    )
    controller: PropertyRef = PropertyRef(
        "controller",
        description="Name of the `ProxmoxSDNController` running the zone's routing protocol. Set for `evpn` zones.",
    )

    # Additional configuration
    ipam: PropertyRef = PropertyRef(
        "ipam",
        description="Name of the IPAM backend the zone allocates guest addresses from, e.g. the built-in `pve` backend.",
    )
    dns: PropertyRef = PropertyRef(
        "dns",
        description="Name of the DNS plugin used to register forward records for guests in this zone.",
    )
    reversedns: PropertyRef = PropertyRef(
        "reversedns",
        description="Name of the DNS plugin used to register reverse (PTR) records for guests in this zone.",
    )
    dnszone: PropertyRef = PropertyRef(
        "dnszone",
        description="DNS domain guest records are created under, e.g. `example.com`.",
    )

    # EVPN specific
    vrf_vxlan: PropertyRef = PropertyRef(
        "vrf_vxlan",
        description="VNI used for an EVPN zone's layer-3 VRF, from the API's `vrf-vxlan` field.",
    )
    vxlan_port: PropertyRef = PropertyRef(
        "vxlan_port",
        description="UDP port used for VXLAN encapsulation, from the API's `vxlan-port` field. Proxmox defaults to 4789.",
    )
    mac: PropertyRef = PropertyRef(
        "mac",
        description="MAC address used for the anycast gateway on the zone's VNets.",
    )

    # QinQ specific
    service_vlan: PropertyRef = PropertyRef(
        "service_vlan",
        description="Outer service VLAN of a `qinq` zone, from the API's `service-vlan` field.",
    )


@dataclass(frozen=True)
class ProxmoxSDNZoneToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNZoneToClusterRel(CartographyRelSchema):
    """
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([VIRTUAL_NETWORK])


# MatchLink Schema for Zone Availability Relationships


@dataclass(frozen=True)
class ProxmoxSDNZoneToNodeMatchLinkProperties(CartographyRelProperties):
    """
    Properties for zone to node AVAILABLE_ON relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxSDNZoneToNodeMatchLink(CartographyRelSchema):
    """
    Connects an SDN zone to the nodes it is restricted to (the zone's
    `nodes` field - see https://pve.proxmox.com/pve-docs/api-viewer/ ->
    /cluster/sdn/zones). A zone with no `nodes` restriction applies to all
    cluster nodes, so no edges are produced for it (see transform_sdn_zone_node_relationships).
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("node_id"),
        }
    )
    source_node_label: str = "ProxmoxSDNZone"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("zone_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AVAILABLE_ON"
    properties: ProxmoxSDNZoneToNodeMatchLinkProperties = (
        ProxmoxSDNZoneToNodeMatchLinkProperties()
    )


# ProxmoxSDNVNet Node Schema


@dataclass(frozen=True)
class ProxmoxSDNVNetNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxSDNVNet node.

    VNets (Virtual Networks) belong to zones and become available as
    Linux bridges on nodes for VM/container connectivity.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this VNet, in the form `{cluster_id}/sdn/vnet/{vnet}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    vnet: PropertyRef = PropertyRef(
        "vnet",
        extra_index=True,
        description="VNet name, at most 8 characters. It becomes the name of the interface guests attach to.",
    )
    zone: PropertyRef = PropertyRef(
        "zone",
        description="Name of the `ProxmoxSDNZone` that provides this VNet's transport.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )

    # VNet configuration
    tag: PropertyRef = PropertyRef(
        "tag", description="VLAN id or VXLAN VNI identifying this VNet inside its zone."
    )
    alias: PropertyRef = PropertyRef(
        "alias", description="Free-text label shown for the VNet in the Proxmox UI."
    )
    vlanaware: PropertyRef = PropertyRef(
        "vlanaware",
        description="True when guests may send 802.1Q-tagged frames on this VNet and the VNet passes the tags through.",
    )

    # Additional configuration
    mac: PropertyRef = PropertyRef(
        "mac", description="MAC address of this VNet's anycast gateway interface."
    )


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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SUBNET])
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

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this subnet. The CIDR's `/` is replaced with `_` so the id stays path-safe.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subnet: PropertyRef = PropertyRef(
        "subnet",
        extra_index=True,
        description="The subnet in CIDR notation, e.g. `10.0.0.0/24`.",
    )
    vnet: PropertyRef = PropertyRef(
        "vnet", description="Name of the `ProxmoxSDNVNet` this subnet is configured on."
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Configuration type discriminator returned by the API, currently always `subnet`.",
    )

    # Subnet configuration
    gateway: PropertyRef = PropertyRef(
        "gateway",
        description="Address inside the subnet that the VNet answers on as the guests' default gateway.",
    )
    snat: PropertyRef = PropertyRef(
        "snat",
        description="True when traffic leaving this subnet is source-NATed to the node's own address.",
    )

    # DHCP configuration
    dhcp_range: PropertyRef = PropertyRef(
        "dhcp_range",
        description="Address ranges Proxmox hands out DHCP leases from for this subnet, from the API's `dhcp-range` field.",
    )

    # DNS configuration
    dnszoneprefix: PropertyRef = PropertyRef(
        "dnszoneprefix",
        description="Prefix prepended to guest names when DNS records are created for this subnet.",
    )


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

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this controller, in the form `{cluster_id}/sdn/controller/{controller}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    controller: PropertyRef = PropertyRef(
        "controller",
        extra_index=True,
        description="Controller name, used as the controller id under /cluster/sdn/controllers.",
    )
    type: PropertyRef = PropertyRef(
        "type", description="Controller type, e.g. `evpn` or `bgp`."
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )

    # BGP/EVPN configuration
    asn: PropertyRef = PropertyRef(
        "asn", description="BGP autonomous system number the controller runs in."
    )
    peers: PropertyRef = PropertyRef(
        "peers",
        description="Comma-separated addresses of the BGP peers the controller establishes sessions with.",
    )
    node: PropertyRef = PropertyRef(
        "node",
        description="Name of the node a `bgp` controller runs on. Null for `evpn` controllers, which are cluster-wide.",
    )

    # Additional EVPN configuration
    ebgp: PropertyRef = PropertyRef(
        "ebgp",
        description="True when the peers sit in a different autonomous system, so the sessions are external BGP.",
    )
    loopback: PropertyRef = PropertyRef(
        "loopback",
        description="Name of the loopback interface used as the source address for BGP sessions.",
    )
    bgp_multipath_as_path_relax: PropertyRef = PropertyRef(
        "bgp_multipath_as_path_relax",
        description="True when BGP multipath accepts paths that traverse different autonomous systems, from the API's `bgp-multipath-as-path-relax` field.",
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

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this IPAM backend, in the form `{cluster_id}/sdn/ipam/{ipam}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ipam: PropertyRef = PropertyRef(
        "ipam",
        extra_index=True,
        description="IPAM backend name, as referenced by `ProxmoxSDNZone.ipam`.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="IPAM plugin type: `pve` for the built-in backend, or `netbox` or `phpipam` for an external service.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )

    # External IPAM configuration
    url: PropertyRef = PropertyRef(
        "url",
        description="Base URL of the external IPAM service. Null for the built-in `pve` backend.",
    )
    # Token is masked to "configured" in transform to avoid storing raw credentials
    token: PropertyRef = PropertyRef(
        "token",
        description="The literal string `configured` when an API token is set for this backend, otherwise null. The token value itself is never ingested.",
    )
    section: PropertyRef = PropertyRef(
        "section", description="phpIPAM section id that addresses are allocated from."
    )


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
