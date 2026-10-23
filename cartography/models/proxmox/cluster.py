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
from cartography.models.ontology.labels import DEVICE_INSTANCE
from cartography.models.ontology.labels import TENANT

# ProxmoxCluster Node Schema


@dataclass(frozen=True)
class ProxmoxClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Name of the Proxmox cluster. For a standalone node, which has no cluster entry in /cluster/status, this is the host name with dots replaced by dashes.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Cluster name from /cluster/status, synthesized from the host name on a standalone node.",
    )
    corosync_version: PropertyRef = PropertyRef(
        "corosync_version",
        description="corosync configuration version integer from /cluster/status, which increments as the cluster membership configuration changes. This is not the Proxmox VE release. Null on a standalone node, where corosync is not running.",
    )
    quorate: PropertyRef = PropertyRef(
        "quorate",
        description="True when the cluster currently has corosync quorum. A cluster without quorum refuses configuration changes. Always true for a standalone node.",
    )
    nodes_online: PropertyRef = PropertyRef(
        "nodes_online",
        description="Number of nodes that /cluster/status currently reports as online.",
    )
    nodes_total: PropertyRef = PropertyRef(
        "nodes_total",
        description="Number of nodes that are members of the cluster, online or not.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to, which on the cluster itself equals `id`. Every Proxmox node type carries it so that analysis and cleanup stay within one cluster.",
    )

    # Cluster options/configuration
    migration_type: PropertyRef = PropertyRef(
        "migration_type",
        description="Transport used for guest migration traffic: `secure` (tunnelled over SSH) or `insecure`.",
    )
    migration_network: PropertyRef = PropertyRef(
        "migration_network",
        description="CIDR of the network that migration traffic is pinned to. Null when migrations use the default cluster network.",
    )
    migration_bandwidth_limit: PropertyRef = PropertyRef(
        "migration_bandwidth_limit",
        description="Default bandwidth cap for cluster transfers such as migration, in KiB/s. Null when transfers are unlimited.",
    )
    console: PropertyRef = PropertyRef(
        "console",
        description="Default console viewer for the web UI: `applet`, `vv`, `html5` or `xtermjs`.",
    )
    email_from: PropertyRef = PropertyRef(
        "email_from",
        description="Sender address used for cluster notification mail. Null when Proxmox uses its default of `root@$hostname`.",
    )
    http_proxy: PropertyRef = PropertyRef(
        "http_proxy",
        description="HTTP proxy Proxmox sends outbound requests such as package and subscription checks through.",
    )
    keyboard: PropertyRef = PropertyRef(
        "keyboard",
        description="Default keyboard layout for consoles opened in this cluster, e.g. `en-us`.",
    )
    language: PropertyRef = PropertyRef(
        "language", description="Default web UI language for this cluster, e.g. `en`."
    )
    mac_prefix: PropertyRef = PropertyRef(
        "mac_prefix",
        description="MAC address prefix Proxmox uses when it generates addresses for guest NICs.",
    )
    max_workers: PropertyRef = PropertyRef(
        "max_workers",
        description="Maximum number of parallel worker tasks one node runs for cluster-wide operations such as bulk migration.",
    )
    next_id_lower: PropertyRef = PropertyRef(
        "next_id_lower",
        description="Lower bound of the VMID range Proxmox picks the next free guest id from.",
    )
    next_id_upper: PropertyRef = PropertyRef(
        "next_id_upper",
        description="Upper bound of the VMID range Proxmox picks the next free guest id from.",
    )

    # Corosync/Totem configuration
    totem_interface: PropertyRef = PropertyRef(
        "totem_interface",
        description="corosync totem interface configuration from /cluster/config, describing the ring links.",
    )
    totem_cluster_name: PropertyRef = PropertyRef(
        "totem_cluster_name",
        description="Cluster name recorded in the corosync totem configuration.",
    )
    totem_config_version: PropertyRef = PropertyRef(
        "totem_config_version",
        description="`config_version` of the corosync configuration file, which increments on every change to it.",
    )
    totem_ip_version: PropertyRef = PropertyRef(
        "totem_ip_version",
        description="IP version corosync uses for ring traffic, e.g. `ipv4-6`.",
    )
    totem_secauth: PropertyRef = PropertyRef(
        "totem_secauth",
        description="corosync `secauth` setting; `on` means ring traffic is authenticated and encrypted.",
    )
    totem_version: PropertyRef = PropertyRef(
        "totem_version", description="Version of the corosync totem protocol in use."
    )


@dataclass(frozen=True)
class ProxmoxClusterSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxCluster node.

    Proxmox clusters are the top-level tenant-like entity.
    No sub_resource_relationship needed as this is the root.
    """

    label: str = "ProxmoxCluster"
    properties: ProxmoxClusterNodeProperties = ProxmoxClusterNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    # No sub_resource_relationship - this is the tenant-like root entity
    sub_resource_relationship: None = None


# ProxmoxNode Node Schema


@dataclass(frozen=True)
class ProxmoxNodeNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxNode.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this node, in the form `{cluster_id}/node/{name}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Proxmox node name, as used in API paths under /nodes.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    hostname: PropertyRef = PropertyRef(
        "hostname",
        description="Host name of the node. Proxmox identifies nodes by host name, so this matches `name`.",
    )
    ip: PropertyRef = PropertyRef(
        "ip",
        description="Address the cluster uses to reach this node, from /cluster/status.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Membership state from /cluster/status: `online`, `offline`, or `unknown` when Proxmox reported none.",
    )
    uptime: PropertyRef = PropertyRef(
        "uptime",
        description="Seconds since the node last booted. 0 when the node is offline.",
    )
    cpu_count: PropertyRef = PropertyRef(
        "cpu_count", description="Number of logical CPUs on the node, from `maxcpu`."
    )
    cpu_usage: PropertyRef = PropertyRef(
        "cpu_usage",
        description="Current CPU utilization as a fraction between 0 and 1.",
    )
    memory_total: PropertyRef = PropertyRef(
        "memory_total", description="Total physical RAM on the node in bytes."
    )
    memory_used: PropertyRef = PropertyRef(
        "memory_used", description="RAM currently in use on the node in bytes."
    )
    disk_total: PropertyRef = PropertyRef(
        "disk_total", description="Total size of the node's root filesystem in bytes."
    )
    disk_used: PropertyRef = PropertyRef(
        "disk_used", description="Space used on the node's root filesystem in bytes."
    )
    level: PropertyRef = PropertyRef(
        "level",
        description="Proxmox VE subscription level of the node. Empty when the node has no subscription.",
    )
    # Additional node information
    kversion: PropertyRef = PropertyRef(
        "kversion",
        description="Running kernel version string from /nodes/{node}/status. Null when the per-node status payload was not collected.",
    )
    loadavg: PropertyRef = PropertyRef(
        "loadavg",
        description="The node's 1, 5 and 15 minute load averages, joined into a comma-separated string.",
    )
    wait: PropertyRef = PropertyRef(
        "wait",
        description="Share of CPU time spent waiting on I/O, as a fraction between 0 and 1, from /nodes/{node}/status.",
    )
    # Swap information
    swap_total: PropertyRef = PropertyRef(
        "swap_total",
        description="Total swap configured on the node in bytes. Null when /nodes/{node}/status was not collected.",
    )
    swap_used: PropertyRef = PropertyRef(
        "swap_used",
        description="Swap currently in use on the node in bytes. Null when /nodes/{node}/status was not collected.",
    )
    swap_free: PropertyRef = PropertyRef(
        "swap_free",
        description="Swap still available on the node in bytes. Null when /nodes/{node}/status was not collected.",
    )
    # Additional system info
    pveversion: PropertyRef = PropertyRef(
        "pveversion",
        description="Proxmox VE version string running on the node, e.g. `pve-manager/8.2.2`.",
    )
    cpuinfo: PropertyRef = PropertyRef(
        "cpuinfo",
        description="CPU model name of the node, flattened from the `cpuinfo.model` field of /nodes/{node}/status.",
    )
    idle: PropertyRef = PropertyRef(
        "idle",
        description="Idle CPU figure reported alongside `wait` by /nodes/{node}/status. Null when that payload was not collected.",
    )


@dataclass(frozen=True)
class ProxmoxNodeToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxNodeToClusterRel(CartographyRelSchema):
    """Nodes belong to clusters."""

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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DEVICE_INSTANCE])


# ProxmoxNodeNetworkInterface Node Schema


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxNodeNetworkInterface.

    Represents physical/virtual network interfaces on Proxmox nodes.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this host interface, combining the node id and the interface name.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Interface name as configured on the host, e.g. `vmbr0`, `eno1` or `bond0`.",
    )
    node_id: PropertyRef = PropertyRef(
        "node_id",
        description="Id of the `ProxmoxNode` this interface is configured on.",
    )
    # Cluster scope, so analysis and cleanup queries can filter this node type the
    # same way they filter every other Proxmox node type.
    cluster_id: PropertyRef = PropertyRef(
        "CLUSTER_ID",
        set_in_kwargs=True,
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Interface kind reported by Proxmox, e.g. `bridge`, `bond`, `eth`, `vlan` or `OVSBridge`.",
    )
    address: PropertyRef = PropertyRef(
        "address",
        description="Statically configured IPv4 address. Null when the interface has no static IPv4 address.",
    )
    netmask: PropertyRef = PropertyRef(
        "netmask", description="IPv4 netmask that goes with `address`."
    )
    gateway: PropertyRef = PropertyRef(
        "gateway", description="IPv4 default gateway configured on this interface."
    )
    address6: PropertyRef = PropertyRef(
        "address6",
        description="Statically configured IPv6 address. Null when the interface has no static IPv6 address.",
    )
    netmask6: PropertyRef = PropertyRef(
        "netmask6", description="IPv6 prefix length that goes with `address6`."
    )
    gateway6: PropertyRef = PropertyRef(
        "gateway6", description="IPv6 default gateway configured on this interface."
    )
    bridge_ports: PropertyRef = PropertyRef(
        "bridge_ports",
        description="Space-separated interfaces enslaved to this bridge. Null on interfaces that are not bridges.",
    )
    bond_slaves: PropertyRef = PropertyRef(
        "bond_slaves",
        description="Space-separated interfaces enslaved to this bond, from the API's `slaves` field. Null on interfaces that are not bonds.",
    )
    active: PropertyRef = PropertyRef(
        "active", description="True when the interface is currently up on the host."
    )
    autostart: PropertyRef = PropertyRef(
        "autostart",
        description="True when the interface is brought up at boot, i.e. marked `auto` in the host's interfaces file.",
    )
    mtu: PropertyRef = PropertyRef(
        "mtu",
        description="Configured MTU in bytes. Null when the interface uses the default.",
    )
    # Additional bond configuration
    bond_mode: PropertyRef = PropertyRef(
        "bond_mode",
        description="Bonding mode of a bond interface, e.g. `balance-rr`, `active-backup` or `802.3ad`.",
    )
    bond_xmit_hash_policy: PropertyRef = PropertyRef(
        "bond_xmit_hash_policy",
        description="Transmit hash policy of an 802.3ad or balance-xor bond, e.g. `layer2+3`.",
    )
    # Additional network config
    cidr: PropertyRef = PropertyRef(
        "cidr",
        description="IPv4 address with prefix length in CIDR notation, as Proxmox reports it.",
    )
    cidr6: PropertyRef = PropertyRef(
        "cidr6",
        description="IPv6 address with prefix length in CIDR notation, as Proxmox reports it.",
    )
    method: PropertyRef = PropertyRef(
        "method",
        description="How IPv4 is configured on the interface: `static`, `dhcp`, `manual` or `none`.",
    )
    method6: PropertyRef = PropertyRef(
        "method6",
        description="How IPv6 is configured on the interface: `static`, `dhcp`, `manual` or `none`.",
    )
    comments: PropertyRef = PropertyRef(
        "comments",
        description="Free-text comment stored with the interface configuration.",
    )


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
