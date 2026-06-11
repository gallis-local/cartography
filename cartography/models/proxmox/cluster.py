"""
Data models for Proxmox clusters and nodes.

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

# ProxmoxCluster Node Schema


@dataclass(frozen=True)
class ProxmoxClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    corosync_version: PropertyRef = PropertyRef("corosync_version")
    quorate: PropertyRef = PropertyRef("quorate")
    nodes_online: PropertyRef = PropertyRef("nodes_online")
    nodes_total: PropertyRef = PropertyRef("nodes_total")
    cluster_id: PropertyRef = PropertyRef("cluster_id")

    # Cluster options/configuration
    migration_type: PropertyRef = PropertyRef("migration_type")
    migration_network: PropertyRef = PropertyRef("migration_network")
    migration_bandwidth_limit: PropertyRef = PropertyRef("migration_bandwidth_limit")
    console: PropertyRef = PropertyRef("console")
    email_from: PropertyRef = PropertyRef("email_from")
    http_proxy: PropertyRef = PropertyRef("http_proxy")
    keyboard: PropertyRef = PropertyRef("keyboard")
    language: PropertyRef = PropertyRef("language")
    mac_prefix: PropertyRef = PropertyRef("mac_prefix")
    max_workers: PropertyRef = PropertyRef("max_workers")
    next_id_lower: PropertyRef = PropertyRef("next_id_lower")
    next_id_upper: PropertyRef = PropertyRef("next_id_upper")

    # Corosync/Totem configuration
    totem_interface: PropertyRef = PropertyRef("totem_interface")
    totem_cluster_name: PropertyRef = PropertyRef("totem_cluster_name")
    totem_config_version: PropertyRef = PropertyRef("totem_config_version")
    totem_ip_version: PropertyRef = PropertyRef("totem_ip_version")
    totem_secauth: PropertyRef = PropertyRef("totem_secauth")
    totem_version: PropertyRef = PropertyRef("totem_version")


@dataclass(frozen=True)
class ProxmoxClusterSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxCluster node.

    Proxmox clusters are the top-level tenant-like entity.
    No sub_resource_relationship needed as this is the root.
    """

    label: str = "ProxmoxCluster"
    properties: ProxmoxClusterNodeProperties = ProxmoxClusterNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    # No sub_resource_relationship - this is the tenant-like root entity
    sub_resource_relationship: None = None


# ProxmoxNode Node Schema


@dataclass(frozen=True)
class ProxmoxNodeNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxNode.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    hostname: PropertyRef = PropertyRef("hostname")
    ip: PropertyRef = PropertyRef("ip")
    status: PropertyRef = PropertyRef("status")
    uptime: PropertyRef = PropertyRef("uptime")
    cpu_count: PropertyRef = PropertyRef("cpu_count")
    cpu_usage: PropertyRef = PropertyRef("cpu_usage")
    memory_total: PropertyRef = PropertyRef("memory_total")
    memory_used: PropertyRef = PropertyRef("memory_used")
    disk_total: PropertyRef = PropertyRef("disk_total")
    disk_used: PropertyRef = PropertyRef("disk_used")
    level: PropertyRef = PropertyRef("level")
    # Additional node information
    kversion: PropertyRef = PropertyRef("kversion")
    loadavg: PropertyRef = PropertyRef("loadavg")
    wait: PropertyRef = PropertyRef("wait")
    # Swap information
    swap_total: PropertyRef = PropertyRef("swap_total")
    swap_used: PropertyRef = PropertyRef("swap_used")
    swap_free: PropertyRef = PropertyRef("swap_free")
    # Additional system info
    pveversion: PropertyRef = PropertyRef("pveversion")
    cpuinfo: PropertyRef = PropertyRef("cpuinfo")
    idle: PropertyRef = PropertyRef("idle")


@dataclass(frozen=True)
class ProxmoxNodeToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxNodeToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxNode)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxNodeToClusterRelProperties = ProxmoxNodeToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxNodeSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxNode.

    Nodes belong to clusters and host VMs/containers.
    """

    label: str = "ProxmoxNode"
    properties: ProxmoxNodeNodeProperties = ProxmoxNodeNodeProperties()
    sub_resource_relationship: ProxmoxNodeToClusterRel = ProxmoxNodeToClusterRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DeviceInstance"])


# ProxmoxNodeNetworkInterface Node Schema


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxNodeNetworkInterface.

    Represents physical/virtual network interfaces on Proxmox nodes.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    node_id: PropertyRef = PropertyRef("node_id")
    type: PropertyRef = PropertyRef("type")
    address: PropertyRef = PropertyRef("address")
    netmask: PropertyRef = PropertyRef("netmask")
    gateway: PropertyRef = PropertyRef("gateway")
    address6: PropertyRef = PropertyRef("address6")
    netmask6: PropertyRef = PropertyRef("netmask6")
    gateway6: PropertyRef = PropertyRef("gateway6")
    bridge_ports: PropertyRef = PropertyRef("bridge_ports")
    bond_slaves: PropertyRef = PropertyRef("bond_slaves")
    active: PropertyRef = PropertyRef("active")
    autostart: PropertyRef = PropertyRef("autostart")
    mtu: PropertyRef = PropertyRef("mtu")
    # Additional bond configuration
    bond_mode: PropertyRef = PropertyRef("bond_mode")
    bond_xmit_hash_policy: PropertyRef = PropertyRef("bond_xmit_hash_policy")
    # Additional network config
    cidr: PropertyRef = PropertyRef("cidr")
    cidr6: PropertyRef = PropertyRef("cidr6")
    method: PropertyRef = PropertyRef("method")
    method6: PropertyRef = PropertyRef("method6")
    comments: PropertyRef = PropertyRef("comments")


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxNodeNetworkInterface)
class ProxmoxNodeNetworkInterfaceToClusterRel(CartographyRelSchema):
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxNodeNetworkInterfaceToClusterRelProperties = (
        ProxmoxNodeNetworkInterfaceToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceToNodeRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNode)-[:HAS_NETWORK_INTERFACE]->(:ProxmoxNodeNetworkInterface)

    Nodes have physical/virtual network interfaces.
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("node_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_NETWORK_INTERFACE"
    properties: ProxmoxNodeNetworkInterfaceToNodeRelProperties = (
        ProxmoxNodeNetworkInterfaceToNodeRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxNodeNetworkInterface.

    Network interfaces belong to nodes.
    """

    label: str = "ProxmoxNodeNetworkInterface"
    properties: ProxmoxNodeNetworkInterfaceNodeProperties = (
        ProxmoxNodeNetworkInterfaceNodeProperties()
    )
    sub_resource_relationship: ProxmoxNodeNetworkInterfaceToClusterRel = (
        ProxmoxNodeNetworkInterfaceToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxNodeNetworkInterfaceToNodeRel(),
        ]
    )
