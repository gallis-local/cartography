"""
Data models for Proxmox compute resources (VMs, containers, disks, network interfaces).

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

# ProxmoxVM Node Schema

@dataclass(frozen=True)
class ProxmoxVMNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxVM node.

    Represents both QEMU VMs and LXC containers.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    vmid: PropertyRef = PropertyRef("vmid", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    node: PropertyRef = PropertyRef("node")
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    type: PropertyRef = PropertyRef("type", extra_index=True)
    status: PropertyRef = PropertyRef("status", extra_index=True)
    template: PropertyRef = PropertyRef("template")
    cpu_cores: PropertyRef = PropertyRef("cpu_cores")
    cpu_sockets: PropertyRef = PropertyRef("cpu_sockets")
    # CPU configuration from VM config (cores/sockets are from detailed config)
    cores: PropertyRef = PropertyRef("cores")
    sockets: PropertyRef = PropertyRef("sockets")
    vcpus: PropertyRef = PropertyRef("vcpus")
    memory: PropertyRef = PropertyRef("memory")
    disk_size: PropertyRef = PropertyRef("disk_size")
    uptime: PropertyRef = PropertyRef("uptime")
    tags: PropertyRef = PropertyRef("tags")
    # Additional VM configuration
    ostype: PropertyRef = PropertyRef("ostype")
    onboot: PropertyRef = PropertyRef("onboot")
    protection: PropertyRef = PropertyRef("protection")
    description: PropertyRef = PropertyRef("description")
    vmgenid: PropertyRef = PropertyRef("vmgenid")
    machine: PropertyRef = PropertyRef("machine")
    bios: PropertyRef = PropertyRef("bios")
    boot: PropertyRef = PropertyRef("boot")
    scsihw: PropertyRef = PropertyRef("scsihw")
    cpu: PropertyRef = PropertyRef("cpu")
    cpulimit: PropertyRef = PropertyRef("cpulimit")
    cpuunits: PropertyRef = PropertyRef("cpuunits")
    hotplug: PropertyRef = PropertyRef("hotplug")
    lock: PropertyRef = PropertyRef("lock")
    # Memory configuration
    balloon: PropertyRef = PropertyRef("balloon")
    shares: PropertyRef = PropertyRef("shares")
    # Advanced CPU/Hardware configuration
    numa: PropertyRef = PropertyRef("numa")
    kvm: PropertyRef = PropertyRef("kvm")
    localtime: PropertyRef = PropertyRef("localtime")
    keyboard: PropertyRef = PropertyRef("keyboard")
    vga: PropertyRef = PropertyRef("vga")
    agent_config: PropertyRef = PropertyRef("agent_config")
    args: PropertyRef = PropertyRef("args")
    # Memory and performance features
    hugepages: PropertyRef = PropertyRef("hugepages")
    keephugepages: PropertyRef = PropertyRef("keephugepages")
    freeze: PropertyRef = PropertyRef("freeze")
    # Hardware devices
    watchdog: PropertyRef = PropertyRef("watchdog")
    rng0: PropertyRef = PropertyRef("rng0")
    audio0: PropertyRef = PropertyRef("audio0")
    efidisk0: PropertyRef = PropertyRef("efidisk0")
    tpmstate0: PropertyRef = PropertyRef("tpmstate0")
    # Device counts (for arrays like hostpci, usb, serial, parallel)
    hostpci_count: PropertyRef = PropertyRef("hostpci_count")
    usb_count: PropertyRef = PropertyRef("usb_count")
    serial_count: PropertyRef = PropertyRef("serial_count")
    parallel_count: PropertyRef = PropertyRef("parallel_count")
    # Guest agent data (optional, requires QEMU guest agent)
    guest_hostname: PropertyRef = PropertyRef("guest_hostname")
    guest_os_name: PropertyRef = PropertyRef("guest_os_name")
    guest_os_version: PropertyRef = PropertyRef("guest_os_version")
    guest_kernel_release: PropertyRef = PropertyRef("guest_kernel_release")
    guest_kernel_version: PropertyRef = PropertyRef("guest_kernel_version")
    guest_machine: PropertyRef = PropertyRef("guest_machine")
    agent_enabled: PropertyRef = PropertyRef("agent_enabled")

@dataclass(frozen=True)
class ProxmoxVMToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxVMToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxVM)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxVMToClusterRelProperties = ProxmoxVMToClusterRelProperties()

@dataclass(frozen=True)
class ProxmoxVMToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxVMToNodeRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNode)-[:HOSTS_VM]->(:ProxmoxVM)

    This is an "other_relationship" showing which node hosts the VM.
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("node_id"),  # Full node ID (cluster_id/node/name)
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HOSTS_VM"
    properties: ProxmoxVMToNodeRelProperties = ProxmoxVMToNodeRelProperties()

@dataclass(frozen=True)
class ProxmoxVMSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxVM.

    VMs belong to clusters and are hosted on nodes.
    """

    label: str = "ProxmoxVM"
    properties: ProxmoxVMNodeProperties = ProxmoxVMNodeProperties()
    sub_resource_relationship: ProxmoxVMToClusterRel = ProxmoxVMToClusterRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxVMToNodeRel(),
        ]
    )

# ProxmoxDisk Node Schema

@dataclass(frozen=True)
class ProxmoxDiskNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxDisk node.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    disk_id: PropertyRef = PropertyRef("disk_id")
    vmid: PropertyRef = PropertyRef("vmid")
    storage: PropertyRef = PropertyRef("storage")
    size: PropertyRef = PropertyRef("size")
    backup: PropertyRef = PropertyRef("backup")
    cache: PropertyRef = PropertyRef("cache")
    # Additional disk configuration
    format: PropertyRef = PropertyRef("format")
    iothread: PropertyRef = PropertyRef("iothread")
    discard: PropertyRef = PropertyRef("discard")
    ssd: PropertyRef = PropertyRef("ssd")
    replicate: PropertyRef = PropertyRef("replicate")
    serial: PropertyRef = PropertyRef("serial")
    wwn: PropertyRef = PropertyRef("wwn")
    snapshot: PropertyRef = PropertyRef("snapshot")
    # Performance limits
    iops: PropertyRef = PropertyRef("iops")
    iops_rd: PropertyRef = PropertyRef("iops_rd")
    iops_wr: PropertyRef = PropertyRef("iops_wr")
    mbps: PropertyRef = PropertyRef("mbps")
    mbps_rd: PropertyRef = PropertyRef("mbps_rd")
    mbps_wr: PropertyRef = PropertyRef("mbps_wr")
    # Burst limits
    mbps_max: PropertyRef = PropertyRef("mbps_max")
    mbps_rd_max: PropertyRef = PropertyRef("mbps_rd_max")
    mbps_wr_max: PropertyRef = PropertyRef("mbps_wr_max")
    iops_max: PropertyRef = PropertyRef("iops_max")
    iops_rd_max: PropertyRef = PropertyRef("iops_rd_max")
    iops_wr_max: PropertyRef = PropertyRef("iops_wr_max")
    # Media and access properties
    media: PropertyRef = PropertyRef("media")
    ro: PropertyRef = PropertyRef("ro")
    detect_zeroes: PropertyRef = PropertyRef("detect_zeroes")

@dataclass(frozen=True)
class ProxmoxDiskToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
# Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxDisk)
class ProxmoxDiskToClusterRel(CartographyRelSchema):
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxDiskToClusterRelProperties = ProxmoxDiskToClusterRelProperties()

@dataclass(frozen=True)
class ProxmoxDiskToVMRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxDiskToVMRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxVM)-[:HAS_DISK]->(:ProxmoxDisk)

    VMs have attached disks. Use vmid + cluster_id to match.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid"),
            "cluster_id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DISK"
    properties: ProxmoxDiskToVMRelProperties = ProxmoxDiskToVMRelProperties()

@dataclass(frozen=True)
class ProxmoxDiskToStorageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxDiskToStorageRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxDisk)-[:STORED_ON]->(:ProxmoxStorage)

    Disks are stored on storage backends.
    """

    target_node_label: str = "ProxmoxStorage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("storage"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STORED_ON"
    properties: ProxmoxDiskToStorageRelProperties = ProxmoxDiskToStorageRelProperties()

@dataclass(frozen=True)
class ProxmoxDiskSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxDisk.

    Disks belong to VMs and are stored on storage backends.
    """

    label: str = "ProxmoxDisk"
    properties: ProxmoxDiskNodeProperties = ProxmoxDiskNodeProperties()
    sub_resource_relationship: ProxmoxDiskToClusterRel = ProxmoxDiskToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxDiskToVMRel(),
            ProxmoxDiskToStorageRel(),
        ]
    )

# ProxmoxNetworkInterface Node Schema

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxNetworkInterface node.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    net_id: PropertyRef = PropertyRef("net_id")
    vmid: PropertyRef = PropertyRef("vmid")
    node_name: PropertyRef = PropertyRef("node_name")
    bridge: PropertyRef = PropertyRef(
        "bridge", extra_index=True
    )
    mac_address: PropertyRef = PropertyRef("mac_address", extra_index=True)
    model: PropertyRef = PropertyRef("model")
    firewall: PropertyRef = PropertyRef(
        "firewall", extra_index=True
    )
    vlan_tag: PropertyRef = PropertyRef(
        "vlan_tag", extra_index=True
    )
    # Additional networking properties
    ip: PropertyRef = PropertyRef("ip", extra_index=True)
    ip6: PropertyRef = PropertyRef("ip6")
    gw: PropertyRef = PropertyRef("gw")
    gw6: PropertyRef = PropertyRef("gw6")
    mtu: PropertyRef = PropertyRef("mtu")
    rate: PropertyRef = PropertyRef("rate")
    link_up: PropertyRef = PropertyRef("link_up")
    # Advanced network configuration
    queues: PropertyRef = PropertyRef("queues")
    trunks: PropertyRef = PropertyRef("trunks")
    tag: PropertyRef = PropertyRef("tag")
    # Guest agent runtime data (actual IPs from running VM)
    actual_ipv4: PropertyRef = PropertyRef("actual_ipv4")
    actual_ipv6: PropertyRef = PropertyRef("actual_ipv6")
    guest_interface_name: PropertyRef = PropertyRef("guest_interface_name")

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
# Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxNetworkInterface)
class ProxmoxNetworkInterfaceToClusterRel(CartographyRelSchema):
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxNetworkInterfaceToClusterRelProperties = (
        ProxmoxNetworkInterfaceToClusterRelProperties()
    )

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToVMRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxVM to ProxmoxNetworkInterface.

    Includes firewall status for quick security queries.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    firewall_enabled: PropertyRef = PropertyRef("firewall")
    interface_slot: PropertyRef = PropertyRef("net_id")

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToVMRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(:ProxmoxNetworkInterface)

    VMs have network interfaces. Use vmid + cluster_id to match.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid"),
            "cluster_id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_NETWORK_INTERFACE"
    properties: ProxmoxNetworkInterfaceToVMRelProperties = (
        ProxmoxNetworkInterfaceToVMRelProperties()
    )

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToBridgeRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxNetworkInterface to ProxmoxNodeNetworkInterface (bridge).

    Tracks which bridge the VM network interface is connected to.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    vlan_tag: PropertyRef = PropertyRef("vlan_tag")

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToBridgeRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNetworkInterface)-[:CONNECTED_TO_BRIDGE]->(:ProxmoxNodeNetworkInterface)

    VM network interfaces connect to node bridge interfaces for network topology.
    This enables lateral movement analysis and network segmentation verification.
    """

    target_node_label: str = "ProxmoxNodeNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("bridge"),
            "node_id": PropertyRef("node_name"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_BRIDGE"
    properties: ProxmoxNetworkInterfaceToBridgeRelProperties = (
        ProxmoxNetworkInterfaceToBridgeRelProperties()
    )

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToVNetRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxNetworkInterface to ProxmoxSDNVNet.

    Tracks which SDN VNet the VM network interface is connected to.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToVNetRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNetworkInterface)-[:CONNECTED_TO_VNET]->(:ProxmoxSDNVNet)

    VM network interfaces connect to SDN VNets when the bridge name matches a VNet ID.
    This enables network segmentation queries and SDN topology analysis.
    """

    target_node_label: str = "ProxmoxSDNVNet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vnet": PropertyRef("bridge"),  # Bridge name is the VNet ID
            "cluster_id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO_VNET"
    properties: ProxmoxNetworkInterfaceToVNetRelProperties = (
        ProxmoxNetworkInterfaceToVNetRelProperties()
    )

@dataclass(frozen=True)
class ProxmoxNetworkInterfaceSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxNetworkInterface.

    Network interfaces belong to VMs and connect to node bridges and SDN VNets.
    """

    label: str = "ProxmoxNetworkInterface"
    properties: ProxmoxNetworkInterfaceNodeProperties = (
        ProxmoxNetworkInterfaceNodeProperties()
    )
    sub_resource_relationship: ProxmoxNetworkInterfaceToClusterRel = (
        ProxmoxNetworkInterfaceToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxNetworkInterfaceToVMRel(),
            ProxmoxNetworkInterfaceToBridgeRel(),
            ProxmoxNetworkInterfaceToVNetRel(),
        ]
    )
