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
from cartography.models.ontology.labels import COMPUTE_INSTANCE

# ProxmoxVM Node Schema


@dataclass(frozen=True)
class ProxmoxVMNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxVM node.

    Represents both QEMU VMs and LXC containers.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this guest, in the form `{cluster_id}/vm/{vmid}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    vmid: PropertyRef = PropertyRef(
        "vmid",
        extra_index=True,
        description="Numeric Proxmox guest id, unique within the cluster.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Guest name: the QEMU `name` for a VM or the host name for a container. Empty when the guest has none.",
    )
    node: PropertyRef = PropertyRef(
        "node", description="Name of the node the guest currently resides on."
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="Guest technology: `qemu` for a virtual machine, `lxc` for a container.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Current run state reported by Proxmox: `running`, `stopped` or `paused`.",
    )
    template: PropertyRef = PropertyRef(
        "template",
        description="True if this guest is a template rather than a runnable VM or container.",
    )
    cpu_cores: PropertyRef = PropertyRef(
        "cpu_cores",
        description="Cores the guest sees: the running guest's `cpus` when available, otherwise the configured `cores`.",
    )
    cpu_sockets: PropertyRef = PropertyRef(
        "cpu_sockets",
        description="Number of CPU sockets presented to the guest. 1 unless configured otherwise.",
    )
    # CPU configuration from VM config (cores/sockets are from detailed config)
    cores: PropertyRef = PropertyRef(
        "cores", description="Configured number of cores per socket."
    )
    sockets: PropertyRef = PropertyRef(
        "sockets", description="Configured number of CPU sockets."
    )
    vcpus: PropertyRef = PropertyRef(
        "vcpus",
        description="Total vCPUs presented to the guest, computed as `cores` times `sockets`. 0 when the core count is unknown.",
    )
    memory: PropertyRef = PropertyRef(
        "memory",
        description="Maximum RAM assigned to the guest in bytes, from `maxmem`.",
    )
    disk_size: PropertyRef = PropertyRef(
        "disk_size",
        description="Guest disk size Proxmox reports in bytes, from `maxdisk`: the rootfs size for a container, the boot disk size for a VM.",
    )
    uptime: PropertyRef = PropertyRef(
        "uptime",
        description="Seconds since the guest started. 0 when the guest is not running.",
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Proxmox tags on the guest, split out of the semicolon-separated `tags` string.",
    )
    # Additional VM configuration
    ostype: PropertyRef = PropertyRef(
        "ostype",
        description="OS type hint in the guest config, e.g. `l26` or `win11` for a VM, or a template OS such as `debian` for a container.",
    )
    onboot: PropertyRef = PropertyRef(
        "onboot",
        description="Proxmox `onboot` flag; 1 starts the guest automatically when its node boots.",
    )
    protection: PropertyRef = PropertyRef(
        "protection",
        description="Proxmox `protection` flag; 1 blocks removal of the guest and its disks.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Free-text notes stored in the guest configuration."
    )
    vmgenid: PropertyRef = PropertyRef(
        "vmgenid",
        description="VM generation id (a UUID) exposed to a QEMU guest so it can tell that it was restored or cloned.",
    )
    machine: PropertyRef = PropertyRef(
        "machine",
        description="QEMU machine type the VM is pinned to, e.g. `q35` or `pc-i440fx-8.1`. Null when Proxmox chooses the default.",
    )
    bios: PropertyRef = PropertyRef(
        "bios",
        description="Firmware the VM boots: `seabios` for legacy BIOS or `ovmf` for UEFI.",
    )
    boot: PropertyRef = PropertyRef(
        "boot", description="Boot order specification, e.g. `order=scsi0;net0`."
    )
    scsihw: PropertyRef = PropertyRef(
        "scsihw",
        description="SCSI controller model presented to the VM, e.g. `virtio-scsi-single`.",
    )
    cpu: PropertyRef = PropertyRef(
        "cpu",
        description="CPU type presented to the guest, e.g. `host`, `kvm64` or `x86-64-v2`, optionally with CPU flags appended.",
    )
    cpulimit: PropertyRef = PropertyRef(
        "cpulimit",
        description="Ceiling on the CPU time the guest may use, in whole CPUs, so 2 allows at most two cores' worth. 0 means no limit.",
    )
    cpuunits: PropertyRef = PropertyRef(
        "cpuunits",
        description="Relative CPU weight the host scheduler gives this guest when guests compete for CPU; a higher value wins a larger share.",
    )
    hotplug: PropertyRef = PropertyRef(
        "hotplug",
        description="Device classes that may be hot-plugged, e.g. `network,disk,usb`. `0` disables hotplug entirely.",
    )
    lock: PropertyRef = PropertyRef(
        "lock",
        description="Operation currently holding a lock on the guest, e.g. `backup`, `migrate` or `snapshot`. Null when the guest is not locked.",
    )
    # Memory configuration
    balloon: PropertyRef = PropertyRef(
        "balloon",
        description="Target RAM in MiB the balloon driver may shrink the guest to under host memory pressure. 0 disables ballooning.",
    )
    shares: PropertyRef = PropertyRef(
        "shares",
        description="Relative weight used when the host reclaims memory through auto-ballooning; a higher value keeps more memory in this guest.",
    )
    # Advanced CPU/Hardware configuration
    numa: PropertyRef = PropertyRef(
        "numa",
        description="Proxmox `numa` flag; 1 exposes a NUMA topology to the guest.",
    )
    kvm: PropertyRef = PropertyRef(
        "kvm",
        description="Proxmox `kvm` flag; 0 disables hardware virtualization so the VM runs fully emulated.",
    )
    localtime: PropertyRef = PropertyRef(
        "localtime",
        description="Proxmox `localtime` flag; 1 presents host local time rather than UTC to the guest's real-time clock.",
    )
    keyboard: PropertyRef = PropertyRef(
        "keyboard",
        description="Keyboard layout for this guest's console, e.g. `en-us`. Null when the cluster default applies.",
    )
    vga: PropertyRef = PropertyRef(
        "vga",
        description="Display device configuration for the VM, e.g. `std`, `qxl` or `serial0`.",
    )
    agent_config: PropertyRef = PropertyRef(
        "agent_config",
        description="Raw QEMU guest agent configuration string from the VM config, e.g. `1,fstrim_cloned_disks=1`.",
    )
    args: PropertyRef = PropertyRef(
        "args", description="Raw `args` string passed through to the QEMU command line."
    )
    # Memory and performance features
    hugepages: PropertyRef = PropertyRef(
        "hugepages",
        description="Huge page size backing the VM's memory: `2` for 2 MiB, `1024` for 1 GiB, or `any`. Null when normal pages are used.",
    )
    keephugepages: PropertyRef = PropertyRef(
        "keephugepages",
        description="Proxmox `keephugepages` flag; 1 keeps the hugepage allocation reserved after the VM stops.",
    )
    freeze: PropertyRef = PropertyRef(
        "freeze",
        description="Proxmox `freeze` flag; 1 starts the VM with its CPU paused so a debugger can attach first.",
    )
    # Hardware devices
    watchdog: PropertyRef = PropertyRef(
        "watchdog",
        description="Watchdog device configuration, e.g. `model=i6300esb,action=reset`. Null when the VM has no watchdog.",
    )
    rng0: PropertyRef = PropertyRef(
        "rng0",
        description="Entropy source configuration for the guest's virtio RNG, e.g. `source=/dev/urandom`.",
    )
    audio0: PropertyRef = PropertyRef(
        "audio0",
        description="Audio device configuration for the VM, e.g. `device=ich9-intel-hda,driver=spice`.",
    )
    efidisk0: PropertyRef = PropertyRef(
        "efidisk0",
        description="Configuration string of the EFI variable disk used by an OVMF/UEFI VM.",
    )
    tpmstate0: PropertyRef = PropertyRef(
        "tpmstate0",
        description="Configuration string of the volume holding the virtual TPM's state.",
    )
    # Device counts (for arrays like hostpci, usb, serial, parallel)
    hostpci_count: PropertyRef = PropertyRef(
        "hostpci_count",
        description="Number of `hostpciN` entries in the config, i.e. how many host PCI devices are passed through to the guest.",
    )
    usb_count: PropertyRef = PropertyRef(
        "usb_count",
        description="Number of `usbN` entries in the config, i.e. how many USB devices are passed through to the guest.",
    )
    serial_count: PropertyRef = PropertyRef(
        "serial_count",
        description="Number of `serialN` serial ports defined on the guest.",
    )
    parallel_count: PropertyRef = PropertyRef(
        "parallel_count",
        description="Number of `parallelN` parallel ports defined on the guest.",
    )
    # Guest agent data (optional, requires QEMU guest agent)
    guest_hostname: PropertyRef = PropertyRef(
        "guest_hostname",
        description="Host name read from inside the guest through the QEMU guest agent. Null when the guest agent is not running.",
    )
    guest_os_name: PropertyRef = PropertyRef(
        "guest_os_name",
        description="OS name reported by the guest agent's `get-osinfo`. Null when the guest agent is not running.",
    )
    guest_os_version: PropertyRef = PropertyRef(
        "guest_os_version",
        description="OS version reported by the guest agent's `get-osinfo`. Null when the guest agent is not running.",
    )
    guest_kernel_release: PropertyRef = PropertyRef(
        "guest_kernel_release",
        description="Kernel release reported by the guest agent. Null when the guest agent is not running.",
    )
    guest_kernel_version: PropertyRef = PropertyRef(
        "guest_kernel_version",
        description="Kernel build string reported by the guest agent. Null when the guest agent is not running.",
    )
    guest_machine: PropertyRef = PropertyRef(
        "guest_machine",
        description="Machine architecture reported by the guest agent, e.g. `x86_64`. Null when the guest agent is not running.",
    )
    agent_enabled: PropertyRef = PropertyRef(
        "agent_enabled",
        description="True when the QEMU guest agent answered during the sync, so the `guest_*` properties hold live data.",
    )


@dataclass(frozen=True)
class ProxmoxVMToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxVMToClusterRel(CartographyRelSchema):
    """VMs belong to clusters."""

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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_INSTANCE])
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

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this disk, in the form `{cluster_id}/vm/{vmid}/disk/{disk_id}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    disk_id: PropertyRef = PropertyRef(
        "disk_id",
        description="Config key the disk is attached as, e.g. `scsi0`, `virtio1`, `rootfs` or `mp0`. Its prefix gives the bus or mount role.",
    )
    vmid: PropertyRef = PropertyRef(
        "vmid", description="Numeric id of the guest this disk is attached to."
    )
    # Cluster scope, so analysis and cleanup queries can filter this node type the
    # same way they filter every other Proxmox node type.
    cluster_id: PropertyRef = PropertyRef(
        "CLUSTER_ID",
        set_in_kwargs=True,
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    storage: PropertyRef = PropertyRef(
        "storage", description="Id of the `ProxmoxStorage` holding this disk's volume."
    )
    size: PropertyRef = PropertyRef(
        "size",
        description="Provisioned size of the disk in bytes, converted from the `size=` suffix in the config.",
    )
    backup: PropertyRef = PropertyRef(
        "backup",
        description="True when the disk is included in vzdump backups of its guest.",
    )
    cache: PropertyRef = PropertyRef(
        "cache",
        description="Host cache mode for the disk: `none`, `writethrough`, `writeback`, `unsafe` or `directsync`.",
    )
    # Additional disk configuration
    format: PropertyRef = PropertyRef(
        "format",
        description="Image format of the volume, e.g. `raw`, `qcow2` or `vmdk`.",
    )
    iothread: PropertyRef = PropertyRef(
        "iothread",
        description="True when the disk is served by its own I/O thread instead of the VM's main event loop.",
    )
    discard: PropertyRef = PropertyRef(
        "discard",
        description="Whether TRIM/UNMAP from the guest is forwarded to the storage; `on` enables it.",
    )
    ssd: PropertyRef = PropertyRef(
        "ssd",
        description="True when the disk is advertised to the guest as non-rotational.",
    )
    replicate: PropertyRef = PropertyRef(
        "replicate",
        description="True when the disk is included in the guest's storage replication jobs.",
    )
    serial: PropertyRef = PropertyRef(
        "serial",
        description="Serial number string presented to the guest for this disk.",
    )
    wwn: PropertyRef = PropertyRef(
        "wwn", description="World Wide Name presented to the guest for this disk."
    )
    snapshot: PropertyRef = PropertyRef(
        "snapshot",
        description="True when the disk runs in qemu snapshot mode, so guest writes are discarded when the VM stops.",
    )
    # Performance limits
    iops: PropertyRef = PropertyRef(
        "iops",
        description="Combined read and write IOPS limit for the disk. Absent when the disk is unthrottled.",
    )
    iops_rd: PropertyRef = PropertyRef(
        "iops_rd",
        description="Read IOPS limit for the disk. Absent when reads are unthrottled.",
    )
    iops_wr: PropertyRef = PropertyRef(
        "iops_wr",
        description="Write IOPS limit for the disk. Absent when writes are unthrottled.",
    )
    mbps: PropertyRef = PropertyRef(
        "mbps",
        description="Combined read and write throughput limit for the disk in MB/s. Absent when the disk is unthrottled.",
    )
    mbps_rd: PropertyRef = PropertyRef(
        "mbps_rd",
        description="Read throughput limit for the disk in MB/s. Absent when reads are unthrottled.",
    )
    mbps_wr: PropertyRef = PropertyRef(
        "mbps_wr",
        description="Write throughput limit for the disk in MB/s. Absent when writes are unthrottled.",
    )
    # Burst limits
    mbps_max: PropertyRef = PropertyRef(
        "mbps_max",
        description="Burst ceiling for combined throughput in MB/s, allowed above `mbps` for short bursts.",
    )
    mbps_rd_max: PropertyRef = PropertyRef(
        "mbps_rd_max",
        description="Burst ceiling for read throughput in MB/s, allowed above `mbps_rd` for short bursts.",
    )
    mbps_wr_max: PropertyRef = PropertyRef(
        "mbps_wr_max",
        description="Burst ceiling for write throughput in MB/s, allowed above `mbps_wr` for short bursts.",
    )
    iops_max: PropertyRef = PropertyRef(
        "iops_max",
        description="Burst ceiling for combined IOPS, allowed above `iops` for short bursts.",
    )
    iops_rd_max: PropertyRef = PropertyRef(
        "iops_rd_max",
        description="Burst ceiling for read IOPS, allowed above `iops_rd` for short bursts.",
    )
    iops_wr_max: PropertyRef = PropertyRef(
        "iops_wr_max",
        description="Burst ceiling for write IOPS, allowed above `iops_wr` for short bursts.",
    )
    # Media and access properties
    media: PropertyRef = PropertyRef(
        "media",
        description="Media type of the config entry. Entries with `media=cdrom` are skipped during ingestion, so CD/DVD mounts never appear as disks.",
    )
    ro: PropertyRef = PropertyRef(
        "ro", description="True when the disk is attached read-only."
    )
    detect_zeroes: PropertyRef = PropertyRef(
        "detect_zeroes",
        description="Whether all-zero writes from the guest are turned into holes or discards; `on` enables it.",
    )


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

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this guest NIC, in the form `{cluster_id}/vm/{vmid}/net/{net_id}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    net_id: PropertyRef = PropertyRef(
        "net_id", description="Config key the NIC is attached as, e.g. `net0`."
    )
    vmid: PropertyRef = PropertyRef(
        "vmid", description="Numeric id of the guest this NIC belongs to."
    )
    node_name: PropertyRef = PropertyRef(
        "node_name",
        description="Name of the node the guest was running on when the NIC was collected.",
    )
    # Cluster scope, so analysis and cleanup queries can filter this node type the
    # same way they filter every other Proxmox node type.
    cluster_id: PropertyRef = PropertyRef(
        "CLUSTER_ID",
        set_in_kwargs=True,
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    bridge: PropertyRef = PropertyRef(
        "bridge",
        extra_index=True,
        description="Host bridge or SDN VNet the NIC is attached to, e.g. `vmbr0`.",
    )
    mac_address: PropertyRef = PropertyRef(
        "mac_address", extra_index=True, description="MAC address assigned to the NIC."
    )
    model: PropertyRef = PropertyRef(
        "model",
        description="NIC model presented to the guest: `virtio`, `e1000`, `rtl8139`, `vmxnet3`, or `veth` for a container interface.",
    )
    firewall: PropertyRef = PropertyRef(
        "firewall",
        extra_index=True,
        description="True when the Proxmox firewall is active on this NIC, so guest-level rules are enforced on its traffic.",
    )
    vlan_tag: PropertyRef = PropertyRef(
        "vlan_tag",
        extra_index=True,
        description="VLAN id the NIC's untagged traffic is placed in. When `trunks` is also set, this is the native VLAN.",
    )
    # Additional networking properties
    ip: PropertyRef = PropertyRef(
        "ip",
        extra_index=True,
        description="Static IPv4 address in CIDR form, or `dhcp`, configured for a container interface. Null for VMs, whose addressing is set inside the guest.",
    )
    ip6: PropertyRef = PropertyRef(
        "ip6",
        description="Static IPv6 address in CIDR form, or `dhcp`/`auto`, configured for a container interface.",
    )
    gw: PropertyRef = PropertyRef(
        "gw", description="IPv4 gateway configured for a container interface."
    )
    gw6: PropertyRef = PropertyRef(
        "gw6", description="IPv6 gateway configured for a container interface."
    )
    mtu: PropertyRef = PropertyRef(
        "mtu",
        description="MTU in bytes configured on the NIC. Null when it inherits the bridge's MTU.",
    )
    rate: PropertyRef = PropertyRef(
        "rate",
        description="Bandwidth cap applied to the NIC in MB/s. Null when the NIC is unthrottled.",
    )
    link_up: PropertyRef = PropertyRef(
        "link_up",
        description="True when the NIC's virtual link is connected. False when the config sets `link_down=1`.",
    )
    # Advanced network configuration
    queues: PropertyRef = PropertyRef(
        "queues",
        description="Number of multiqueue pairs on a virtio NIC. Null when multiqueue is off.",
    )
    trunks: PropertyRef = PropertyRef(
        "trunks",
        description="Semicolon-separated VLAN ids trunked to this NIC when it is VLAN-aware.",
    )
    tag: PropertyRef = PropertyRef(
        "tag",
        description="Native VLAN id, mirrored from `vlan_tag` and only set when `trunks` is present.",
    )
    # Guest agent runtime data (actual IPs from running VM)
    actual_ipv4: PropertyRef = PropertyRef(
        "actual_ipv4",
        description="Comma-separated IPv4 addresses in CIDR form actually configured inside the guest, read through the QEMU guest agent. Null when the guest agent is not running.",
    )
    actual_ipv6: PropertyRef = PropertyRef(
        "actual_ipv6",
        description="Comma-separated IPv6 addresses in CIDR form actually configured inside the guest, read through the QEMU guest agent. Null when the guest agent is not running.",
    )
    guest_interface_name: PropertyRef = PropertyRef(
        "guest_interface_name",
        description="Interface name as seen inside the guest, e.g. `eth0`, from the QEMU guest agent. Null when the guest agent is not running.",
    )


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
    firewall_enabled: PropertyRef = PropertyRef(
        "firewall", description="True when the Proxmox firewall is active on this NIC."
    )
    interface_slot: PropertyRef = PropertyRef(
        "net_id", description="Config key the NIC occupies on the guest, e.g. `net0`."
    )


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToVMRel(CartographyRelSchema):
    """
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
    vlan_tag: PropertyRef = PropertyRef(
        "vlan_tag",
        description="VLAN id the NIC's traffic carries on this bridge. Null when the NIC is untagged.",
    )


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToBridgeRel(CartographyRelSchema):
    """
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
