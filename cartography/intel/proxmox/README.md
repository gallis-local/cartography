# Proxmox Virtual Environment Integration

This module syncs Proxmox Virtual Environment (PVE) infrastructure into Cartography, enabling infrastructure asset tracking across Proxmox clusters.

## Features

The Proxmox integration syncs the following resources:

- **Clusters and Nodes**: Physical/virtual nodes in your Proxmox cluster
- **Virtual Machines**: QEMU/KVM virtual machines with detailed configuration
- **Containers**: LXC containers with resource allocation
- **Snapshots**: VM and container snapshots for backup and recovery
- **Disks**: Virtual disk configurations and storage relationships
- **Network Interfaces**: VM network interfaces with VLAN and bridge information
- **Storage**: Storage backends (local, NFS, Ceph, LVM, etc.)
- **Resource Pools**: Pool-based organization of VMs, containers, and storage
- **Backup Jobs**: Scheduled backup configurations with retention policies
- **Replication Jobs**: VM/container replication schedules between nodes
- **High Availability**: HA groups and resource configurations for failover
- **Access Control**: Users, groups, roles, ACL permissions, and API tokens
- **Authentication Realms**: PAM, LDAP, AD, and other authentication backends
- **Firewall Rules**: Cluster, node, and VM-level firewall configurations
- **Firewall Options**: Global firewall configuration settings
- **SSL Certificates**: TLS certificate tracking and expiration monitoring

## Configuration

### Prerequisites

1. **Proxmox VE 7.0+** (tested with 8.x/9.x)
2. **API Token or User Credentials**
3. **Permissions**: Read-only access is sufficient (`PVEAuditor` role recommended)

### Setup

#### Option 1: API Token Authentication (Recommended)

1. Create an API token in Proxmox:
   - Navigate to Datacenter → Permissions → API Tokens
   - Create a new token for user `root@pam` with name `cartography`
   - Grant the `PVEAuditor` role on `/`
   - Save the token value securely

2. Set environment variables:
   ```bash
   export PROXMOX_TOKEN_NAME="cartography"
   export PROXMOX_TOKEN_VALUE="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
   ```

3. Run Cartography:
   ```bash
   cartography --neo4j-uri bolt://localhost:7687 \
       --proxmox-host proxmox.example.com \
       --proxmox-user root@pam \
       --proxmox-token-name-env-var PROXMOX_TOKEN_NAME \
       --proxmox-token-value-env-var PROXMOX_TOKEN_VALUE
   ```

#### Option 2: Password Authentication

1. Set environment variable:
   ```bash
   export PROXMOX_PASSWORD="your-password"
   ```

2. Run Cartography:
   ```bash
   cartography --neo4j-uri bolt://localhost:7687 \
       --proxmox-host proxmox.example.com \
       --proxmox-user root@pam \
       --proxmox-password-env-var PROXMOX_PASSWORD
   ```

## Schema

### Node Types

#### ProxmoxCluster
- `id`: Cluster identifier
- `name`: Cluster name
- `version`: Proxmox VE version
- `quorate`: Cluster quorum status
- `nodes_online`: Number of online nodes
- `nodes_total`: Total number of nodes in cluster
- `cluster_id`: Internal cluster ID from API
- **Migration settings:**
  - `migration_type`: Migration mode (secure, insecure)
  - `migration_network`: CIDR network used for VM migrations
  - `migration_bandwidth_limit`: Bandwidth limit for migrations in KB/s
- **Console and UI settings:**
  - `console`: Default console viewer (html5, vv, xtermjs)
  - `keyboard`: Default keyboard layout
  - `language`: Default language setting
- **Email and proxy:**
  - `email_from`: Default email sender address
  - `http_proxy`: HTTP proxy URL if configured
- **Resource management:**
  - `mac_prefix`: MAC address prefix for VMs
  - `max_workers`: Maximum parallel migration workers
  - `next_id_lower`, `next_id_upper`: Auto-assigned VM ID bounds
- **Corosync/Totem configuration:**
  - `totem_cluster_name`: Cluster name from corosync
  - `totem_config_version`: Corosync config version
  - `totem_interface`: Network interface used by totem
  - `totem_ip_version`: IP version (ipv4/ipv6)
  - `totem_secauth`: Security authentication enabled
  - `totem_version`: Totem protocol version

#### ProxmoxNode
- `id`: Node name (unique)
- `name`: Node display name
- `hostname`: Node hostname
- `ip`: Management IP address
- `status`: online/offline/unknown
- `uptime`: Node uptime in seconds
- **CPU information:**
  - `cpu_count`: Number of CPU cores
  - `cpu_usage`: CPU utilization (0.0 to 1.0)
  - `cpuinfo`: CPU model information
  - `idle`: Idle CPU percentage
- **Memory information:**
  - `memory_total`, `memory_used`: RAM in bytes
  - `swap_total`, `swap_used`, `swap_free`: Swap space in bytes
- **Disk information:**
  - `disk_total`, `disk_used`: Disk space in bytes
- **System information:**
  - `kversion`: Kernel version
  - `pveversion`: Proxmox VE version string
  - `loadavg`: Load average (CSV: 1m, 5m, 15m)
  - `wait`: I/O wait percentage
- `level`: Node level in cluster

#### ProxmoxNodeNetworkInterface
- `id`: Unique identifier
- `name`: Interface name (e.g., vmbr0, eth0)
- `node_name`: Name of the node this interface belongs to
- `type`: Interface type (bridge, bond, eth, vlan, etc.)
- **IPv4 configuration:**
  - `address`: IPv4 address
  - `netmask`: IPv4 subnet mask
  - `gateway`: IPv4 default gateway
  - `cidr`: CIDR notation (e.g., 192.168.1.10/24)
  - `method`: Configuration method (static, dhcp, manual)
- **IPv6 configuration:**
  - `address6`, `netmask6`, `gateway6`: IPv6 settings
  - `cidr6`: IPv6 CIDR notation
  - `method6`: IPv6 configuration method
- **Bridge configuration:**
  - `bridge_ports`: Bridge member ports
- **Bond configuration:**
  - `bond_slaves`: Bond slave interfaces
  - `bond_mode`: Bonding mode (balance-rr, active-backup, 802.3ad, etc.)
  - `bond_xmit_hash_policy`: Bond transmit hash policy (layer2, layer3+4, etc.)
- **Status and settings:**
  - `active`: Boolean indicating if interface is active
  - `autostart`: Boolean indicating if interface auto-starts on boot
  - `mtu`: MTU size
  - `comments`: Interface comments/description

#### ProxmoxVM
- `id`: Format `node/type/vmid` (e.g., `node1/qemu/100`)
- `vmid`: VM ID number
- `name`: VM name
- `type`: qemu or lxc
- `status`: running/stopped/paused
- `cpu_cores`, `cpu_sockets`: CPU configuration
- `memory`: RAM in bytes
- `tags`: Array of VM tags

#### ProxmoxDisk
- `id`: Format `node/type/vmid:disk_id` (e.g., `node1/qemu/100:scsi0`)
- `disk_id`: Disk identifier (e.g., scsi0, virtio0, sata0, ide0, efidisk0, tpmstate0, rootfs)
- `storage`: Storage backend ID
- `size`: Size in bytes
- `backup`: Backup enabled flag

#### ProxmoxNetworkInterface
- `id`: Format `node/type/vmid:net_id` (e.g., `node1/qemu/100:net0`)
- `net_id`: Network interface identifier (e.g., net0, net1)
- `bridge`: Bridge name
- `mac_address`: MAC address
- `model`: Network adapter model (e.g., virtio, e1000, rtl8139, vmxnet3, veth)
- `firewall`: Boolean indicating if Proxmox firewall is enabled
- `vlan_tag`: VLAN tag if configured
- `ip`: IPv4 address assigned to the interface
- `ip6`: IPv6 address assigned to the interface
- `gw`: IPv4 gateway
- `gw6`: IPv6 gateway
- `mtu`: MTU size
- `rate`: Bandwidth rate limit (in MB/s)
- `link_up`: Boolean indicating if the link is up

#### ProxmoxStorage
- `id`: Storage ID
- `type`: Storage type (dir, nfs, lvm, ceph, etc.)
- `content_types`: Array of content types
- `shared`: Shared storage flag
- `total`, `used`, `available`: Space information

#### ProxmoxPool
- `id`: Pool identifier
- `poolid`: Pool name
- `comment`: Description/notes

#### ProxmoxBackupJob
- `id`: Job identifier
- `schedule`: Cron-style schedule
- `storage`: Target storage backend
- `enabled`: Job enabled/disabled
- `mode`: Backup mode (snapshot, suspend, stop)
- `compression`: Compression type (zstd, gzip, lzo)
- `prune_keep_last`, `prune_keep_daily`, etc.: Retention policy settings

#### ProxmoxHAGroup
- `id`: Group identifier
- `group`: Group name
- `nodes`: Comma-separated list of preferred nodes
- `restricted`: Whether to restrict to listed nodes
- `nofailback`: Prevent automatic failback

#### ProxmoxHAResource
- `id`: Resource identifier (e.g., vm:100)
- `sid`: Service ID
- `state`: Current state (started, stopped, disabled)
- `group`: Associated HA group
- `max_restart`: Maximum restart attempts
- `max_relocate`: Maximum relocation attempts

#### ProxmoxUser
- `id`: User identifier (format: user@realm)
- `userid`: Full user ID
- `enable`: Account enabled flag
- `email`: Email address
- `firstname`, `lastname`: User names
- `groups`: Array of group memberships
- `tokens`: Array of API tokens

#### ProxmoxGroup
- `id`: Group identifier
- `groupid`: Group name
- `comment`: Description

#### ProxmoxRole
- `id`: Role identifier
- `roleid`: Role name
- `privs`: Array of privileges
- `special`: Built-in role flag

#### ProxmoxACL
- `id`: ACL entry identifier
- `path`: Resource path (e.g., /, /vms/100)
- `roleid`: Role granted
- `ugid`: User or group ID
- `propagate`: Propagate to children flag

#### ProxmoxFirewallRule
- `id`: Rule identifier
- `scope`: Rule scope (cluster, node, vm)
- `pos`: Position in rule list
- `type`: Rule type (in, out, group)
- `action`: Action (ACCEPT, DROP, REJECT)
- `source`, `dest`: Source/destination addresses
- `proto`: Protocol (tcp, udp, icmp)
- `dport`, `sport`: Destination/source ports

#### ProxmoxFirewallIPSet
- `id`: IP set identifier
- `name`: IP set name
- `scope`: Scope (cluster, node, vm)
- `cidrs`: Array of CIDR entries

#### ProxmoxCertificate
- `id`: Certificate identifier
- `node_name`: Node using this certificate
- `fingerprint`: Certificate fingerprint
- `issuer`, `subject`: Certificate fields
- `notbefore`, `notafter`: Validity period
- `san`: Subject Alternative Names array

#### ProxmoxSnapshot
- `id`: Snapshot identifier
- `name`: Snapshot name
- `cluster_id`: Parent cluster ID
- `vmid`: VM/container ID
- `vm_type`: VM type (qemu or lxc)
- `node`: Node name where VM resides
- `description`: Snapshot description
- `snaptime`: Unix timestamp of snapshot creation
- `vmstate`: Whether VM state is included (QEMU only)
- `parent`: Parent snapshot name (for snapshot chains)

#### ProxmoxAPIToken
- `id`: Token identifier
- `tokenid`: Token name
- `full_tokenid`: Full token ID (format: user@realm!tokenid)
- `cluster_id`: Parent cluster ID
- `userid`: Associated user ID
- `comment`: Token description
- `expire`: Expiration timestamp (0 = never expires)
- `privsep`: Privilege separation enabled flag

#### ProxmoxReplicationJob
- `id`: Job identifier
- `job_id`: Proxmox job ID (format: vmid-number)
- `cluster_id`: Parent cluster ID
- `type`: Replication type (local)
- `target`: Target node name
- `source`: Source node name
- `guest`: VM/container ID being replicated
- `schedule`: Cron-style schedule
- `rate`: Rate limit in MB/s
- `comment`: Job description
- `enabled`: Job enabled/disabled flag

#### ProxmoxAuthRealm
- `id`: Realm identifier
- `realm`: Realm name
- `cluster_id`: Parent cluster ID
- `type`: Realm type (pam, ldap, ad, pve, openid)
- `comment`: Realm description
- `default`: Whether this is the default realm
- `tfa`: Two-factor authentication type (oath, yubico, etc.)

#### ProxmoxFirewallOptions
- `id`: Options identifier
- `cluster_id`: Parent cluster ID
- `scope`: Scope (cluster or node)
- `scope_id`: Node name (for node-level options)
- `enable`: Firewall enabled/disabled
- `policy_in`: Default incoming policy (ACCEPT, REJECT, DROP)
- `policy_out`: Default outgoing policy
- `log_level_in`: Log level for incoming traffic
- `log_level_out`: Log level for outgoing traffic
- `nf_conntrack_max`: Maximum connection tracking entries
- `nf_conntrack_tcp_timeout_established`: TCP established timeout

### Relationships

```
(:ProxmoxNode)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxNode)-[:HOSTS_VM]->(:ProxmoxVM)
(:ProxmoxNode)-[:HAS_NETWORK_INTERFACE]->(:ProxmoxNodeNetworkInterface)
(:ProxmoxVM)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxVM)-[:HAS_DISK]->(:ProxmoxDisk)
(:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(:ProxmoxNetworkInterface)
(:ProxmoxDisk)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxDisk)-[:STORED_ON]->(:ProxmoxStorage)
(:ProxmoxNetworkInterface)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxNodeNetworkInterface)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxStorage)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxStorage)-[:AVAILABLE_ON]->(:ProxmoxNode)
(:ProxmoxPool)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxPool)-[:CONTAINS_VM]->(:ProxmoxVM)
(:ProxmoxPool)-[:CONTAINS_STORAGE]->(:ProxmoxStorage)
(:ProxmoxBackupJob)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxBackupJob)-[:BACKS_UP]->(:ProxmoxVM)
(:ProxmoxBackupJob)-[:BACKS_UP_TO]->(:ProxmoxStorage)
(:ProxmoxHAGroup)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxHAResource)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxHAResource)-[:MEMBER_OF_HA_GROUP]->(:ProxmoxHAGroup)
(:ProxmoxHAResource)-[:PROTECTS]->(:ProxmoxVM)
(:ProxmoxUser)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxUser)-[:MEMBER_OF_GROUP]->(:ProxmoxGroup)
(:ProxmoxGroup)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxRole)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxACL)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxACL)-[:GRANTS_ROLE]->(:ProxmoxRole)
(:ProxmoxACL)-[:APPLIES_TO_USER]->(:ProxmoxUser)
(:ProxmoxACL)-[:APPLIES_TO_GROUP]->(:ProxmoxGroup)
(:ProxmoxACL)-[:GRANTS_ACCESS_TO]->(:ProxmoxVM|:ProxmoxStorage|:ProxmoxPool|:ProxmoxNode|:ProxmoxCluster)
(:ProxmoxUser)-[:HAS_PERMISSION]->(:ProxmoxVM|:ProxmoxStorage|:ProxmoxPool|:ProxmoxNode|:ProxmoxCluster)
(:ProxmoxGroup)-[:HAS_PERMISSION]->(:ProxmoxVM|:ProxmoxStorage|:ProxmoxPool|:ProxmoxNode|:ProxmoxCluster)
(:ProxmoxFirewallRule)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxFirewallRule)-[:APPLIES_TO_NODE]->(:ProxmoxNode)
(:ProxmoxFirewallRule)-[:APPLIES_TO_VM]->(:ProxmoxVM)
(:ProxmoxFirewallRule)-[:USES_IPSET]->(:ProxmoxFirewallIPSet)
(:ProxmoxFirewallIPSet)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxCertificate)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxNode)-[:HAS_CERTIFICATE]->(:ProxmoxCertificate)
(:ProxmoxSnapshot)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxSnapshot)-[:SNAPSHOT_OF]->(:ProxmoxVM)
(:ProxmoxAPIToken)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxAPIToken)-[:ASSOCIATED_WITH]->(:ProxmoxUser)
(:ProxmoxReplicationJob)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxAuthRealm)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxFirewallOptions)-[:RESOURCE]->(:ProxmoxCluster)
(:ProxmoxNetworkInterface)-[:CONNECTED_TO_BRIDGE]->(:ProxmoxNodeNetworkInterface)
(:ProxmoxVM)-[:NETWORK_ADJACENT]-(:ProxmoxVM)
```

### Data Model Diagram

```
                                      ┌─────────────────────┐
                                      │   ProxmoxCluster    │
                                      │    (Root/Tenant)    │
                                      └──────────┬──────────┘
                                                 │ [:RESOURCE] (all nodes)
       ┌────────────────┬────────────────┬───────┴───────┬────────────────┬────────────────┐
       │                │                │               │                │                │
       ▼                ▼                ▼               ▼                ▼                ▼
┌─────────────┐  ┌───────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  ┌─────────────┐
│ ProxmoxNode │  │ProxmoxPool│  │ProxmoxStorage│  │ProxmoxRole│  │ProxmoxBackupJob│ │ProxmoxHAGroup│
└──────┬──────┘  └─────┬─────┘  └──────┬───────┘  └─────┬─────┘  └───────┬───────┘  └──────┬──────┘
       │               │               │                │                │                 │
       │               │               │                │                │                 │
┌──────┼──────┐  CONTAINS_VM    AVAILABLE_ON      GRANTS_ROLE      BACKS_UP         MEMBER_OF
│      │      │        │               │                │                │                 │
│      │      │        │               │                │                │                 │
▼      ▼      ▼        │               │                │                │                 ▼
NodeNI Cert HOSTS_VM   │               │                │                │         ┌─────────────────┐
              │        │               │                ▼                │         │ProxmoxHAResource│
              │        │               │         ┌─────────────┐         │         └────────┬────────┘
              │        │               │         │ ProxmoxACL  │         │                  │
              │        │               │         └──────┬──────┘         │             PROTECTS
              │        │               │                │                │                  │
              ▼        ▼               ▼                │                ▼                  │
       ┌──────────────────────────────────────────┐     │     ┌──────────────────────┐      │
       │                 ProxmoxVM                │◄────┼─────│      BACKS_UP        │      │
       │          (QEMU VMs & LXC Containers)     │◄────┼─────│   GRANTS_ACCESS_TO   │◄─────┘
       └─────────────────────┬────────────────────┘     │     │    HAS_PERMISSION    │
                             │                          │     └──────────────────────┘
               ┌─────────────┴─────────────┐            │
               │                           │            │
               ▼                           ▼            │
        ┌────────────┐              ┌──────────┐        │
        │ProxmoxDisk │              │ VMNetIF  │        │
        └─────┬──────┘              └──────────┘        │
              │                                         │
              │ STORED_ON                               │
              ▼                                         │
        ┌──────────────┐◄───────────────────────────────┤
        │ProxmoxStorage│ ◄── BACKS_UP_TO                │
        └──────────────┘ ◄── GRANTS_ACCESS_TO           │
              ▲          ◄── HAS_PERMISSION             │
              │                                         │
         CONTAINS_STORAGE                               │
              │                                         │
        ┌─────┴─────┐                                   │
        │ProxmoxPool│ ◄── GRANTS_ACCESS_TO ─────────────┤
        └───────────┘ ◄── HAS_PERMISSION                │
                                                        │
                                                        │
    ══════════════════════════════════════════════════════════════════════
    ACCESS CONTROL (RBAC)                               │
    ══════════════════════════════════════════════════════════════════════
                                                        │
        ┌─────────────────────┐                         │
        │     ProxmoxACL      │─────────────────────────┘
        └──────────┬──────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   APPLIES_TO_USER │    APPLIES_TO_GROUP
        │          │          │
        ▼          │          ▼
  ┌───────────┐    │    ┌─────────────┐
  │ProxmoxUser│    │    │ProxmoxGroup │
  └─────┬─────┘    │    └──────┬──────┘
        │          │           │
        │   MEMBER_OF_GROUP    │
        └──────────►───────────┘
        │                      │
        │    HAS_PERMISSION    │
        └──────────────────────┴─────────► (VM, Storage, Pool, Node, Cluster)


    ══════════════════════════════════════════════════════════════════════
    SECURITY
    ══════════════════════════════════════════════════════════════════════

    ┌────────────────────┐          ┌────────────────────┐
    │ProxmoxFirewallRule │          │ProxmoxFirewallIPSet│
    └─────────┬──────────┘          └────────────────────┘
              │
     APPLIES_TO_NODE / APPLIES_TO_VM
              │
              ▼
        ProxmoxNode / ProxmoxVM


LEGEND:
═══════
  NodeNI  = ProxmoxNodeNetworkInterface
  VMNetIF = ProxmoxNetworkInterface (VM network interface)
  Cert    = ProxmoxCertificate

  ───►  = Relationship direction
  ◄───  = Relationship target (incoming)

  All nodes connect to ProxmoxCluster via [:RESOURCE] relationship
```

### Relationship Categories

#### Infrastructure Layer
| From | Relationship | To | Description |
|------|-------------|-----|-------------|
| ProxmoxNode | RESOURCE | ProxmoxCluster | Node belongs to cluster |
| ProxmoxNode | HOSTS_VM | ProxmoxVM | Node hosts VM/container |
| ProxmoxNode | HAS_NETWORK_INTERFACE | ProxmoxNodeNetworkInterface | Node has physical/bridge interface |
| ProxmoxNode | HAS_CERTIFICATE | ProxmoxCertificate | Node uses SSL certificate |

#### Compute Layer
| From | Relationship | To | Description |
|------|-------------|-----|-------------|
| ProxmoxVM | RESOURCE | ProxmoxCluster | VM belongs to cluster |
| ProxmoxVM | HAS_DISK | ProxmoxDisk | VM has attached disk |
| ProxmoxVM | HAS_NETWORK_INTERFACE | ProxmoxNetworkInterface | VM has network interface |
| ProxmoxDisk | STORED_ON | ProxmoxStorage | Disk stored on storage backend |

#### Storage & Organization
| From | Relationship | To | Description |
|------|-------------|-----|-------------|
| ProxmoxStorage | AVAILABLE_ON | ProxmoxNode | Storage available on node(s) |
| ProxmoxPool | CONTAINS_VM | ProxmoxVM | Pool contains VM |
| ProxmoxPool | CONTAINS_STORAGE | ProxmoxStorage | Pool contains storage |

#### Backup & High Availability
| From | Relationship | To | Description |
|------|-------------|-----|-------------|
| ProxmoxSnapshot | SNAPSHOT_OF | ProxmoxVM | Snapshot is of VM/container |
| ProxmoxBackupJob | BACKS_UP | ProxmoxVM | Job backs up VM |
| ProxmoxBackupJob | BACKS_UP_TO | ProxmoxStorage | Job stores backups to storage |
| ProxmoxReplicationJob | RESOURCE | ProxmoxCluster | Replication job belongs to cluster |
| ProxmoxHAResource | MEMBER_OF_HA_GROUP | ProxmoxHAGroup | HA resource assigned to group |
| ProxmoxHAResource | PROTECTS | ProxmoxVM | HA protects VM |

#### Access Control (RBAC)
| From | Relationship | To | Description |
|------|-------------|-----|-------------|
| ProxmoxUser | MEMBER_OF_GROUP | ProxmoxGroup | User is member of group |
| ProxmoxAPIToken | ASSOCIATED_WITH | ProxmoxUser | API token belongs to user |
| ProxmoxAuthRealm | RESOURCE | ProxmoxCluster | Auth realm belongs to cluster |
| ProxmoxACL | GRANTS_ROLE | ProxmoxRole | ACL grants role permissions |
| ProxmoxACL | APPLIES_TO_USER | ProxmoxUser | ACL applies to user |
| ProxmoxACL | APPLIES_TO_GROUP | ProxmoxGroup | ACL applies to group |
| ProxmoxACL | GRANTS_ACCESS_TO | ProxmoxVM/Storage/Pool/Node/Cluster | ACL grants access to resource |

#### Derived Permission Relationships
| From | Relationship | To | Description |
|------|-------------|-----|-------------|
| ProxmoxUser | HAS_PERMISSION | ProxmoxVM/Storage/Pool/Node/Cluster | User has effective permission on resource |
| ProxmoxGroup | HAS_PERMISSION | ProxmoxVM/Storage/Pool/Node/Cluster | Group has effective permission on resource |

These derived `HAS_PERMISSION` relationships include metadata:
- `via_acl`: The ACL that granted this permission
- `role`: The role being granted
- `privileges`: Array of specific privileges
- `path`: Original ACL path
- `propagate`: Whether permission propagates to children
- `via_group`: True if permission is inherited through group membership

#### Security
| From | Relationship | To | Description |
|------|-------------|-----|-------------|
| ProxmoxFirewallRule | APPLIES_TO_NODE | ProxmoxNode | Rule applies to node |
| ProxmoxFirewallRule | APPLIES_TO_VM | ProxmoxVM | Rule applies to VM |
| ProxmoxFirewallRule | USES_IPSET | ProxmoxFirewallIPSet | Rule references IPSet in source/dest |
| ProxmoxFirewallOptions | RESOURCE | ProxmoxCluster | Firewall options belong to cluster |

#### Network Topology
| From | Relationship | To | Description |
|------|-------------|-----|-------------|
| ProxmoxNetworkInterface | CONNECTED_TO_BRIDGE | ProxmoxNodeNetworkInterface | VM NIC connects to node bridge |
| ProxmoxVM | NETWORK_ADJACENT | ProxmoxVM | VMs on same bridge/VLAN (bidirectional) |

The `NETWORK_ADJACENT` relationship includes properties:
- `bridge`: The shared bridge name
- `vlan_tag`: The shared VLAN tag (null if untagged)

## Example Queries

### Find all running VMs
```cypher
MATCH (v:ProxmoxVM)
WHERE v.status = 'running'
RETURN v.name, v.node, v.memory, v.cpu_cores
```

### Find VMs with internet-facing interfaces
```cypher
MATCH (v:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(i:ProxmoxNetworkInterface)
WHERE i.bridge = 'vmbr0' AND v.status = 'running'
RETURN v.name, i.mac_address, i.bridge
```

### Find nodes with high CPU usage
```cypher
MATCH (n:ProxmoxNode)
WHERE n.cpu_usage > 0.8
RETURN n.name, n.cpu_usage, n.status
ORDER BY n.cpu_usage DESC
```

### Find VMs by tag
```cypher
MATCH (v:ProxmoxVM)
WHERE 'production' IN v.tags
RETURN v.name, v.node, v.tags
```

### Find VMs with firewall disabled on any interface
```cypher
MATCH (vm:ProxmoxVM)-[r:HAS_NETWORK_INTERFACE]->(ni:ProxmoxNetworkInterface)
WHERE r.firewall_enabled = false OR ni.firewall = false
RETURN vm.name, ni.net_id, ni.bridge, ni.vlan_tag
ORDER BY vm.name
```

### Lateral movement analysis: Find VMs reachable from a compromised VM
```cypher
MATCH path = (source:ProxmoxVM {name: 'compromised-vm'})-[:NETWORK_ADJACENT*1..3]-(target:ProxmoxVM)
WHERE source <> target
RETURN DISTINCT target.name, target.status, length(path) as hops
ORDER BY hops, target.name
```

### Find VMs on the same network segment
```cypher
MATCH (vm1:ProxmoxVM)-[:NETWORK_ADJACENT]-(vm2:ProxmoxVM)
RETURN vm1.name, vm2.name,
       [(vm1)-[:NETWORK_ADJACENT]-(vm2) | vm1][0].name as bridge
ORDER BY vm1.name, vm2.name
```

### Find VMs connected to a specific bridge
```cypher
MATCH (vm:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(ni:ProxmoxNetworkInterface)
      -[:CONNECTED_TO_BRIDGE]->(bridge:ProxmoxNodeNetworkInterface)
WHERE bridge.name = 'vmbr0'
RETURN vm.name, ni.mac_address, ni.vlan_tag, bridge.node_name
ORDER BY vm.name
```

### Find all storage backends and their capacity
```cypher
MATCH (s:ProxmoxStorage)
RETURN s.name, s.type, s.total, s.used, s.available
ORDER BY s.used DESC
```

### Find VMs in a specific pool
```cypher
MATCH (pool:ProxmoxPool {poolid: 'production'})-[:CONTAINS_VM]->(vm:ProxmoxVM)
RETURN vm.name, vm.status, vm.node
ORDER BY vm.name
```

### Find all backup jobs for a VM
```cypher
MATCH (vm:ProxmoxVM {name: 'my-vm'})<-[:BACKS_UP]-(job:ProxmoxBackupJob)
RETURN job.id, job.schedule, job.enabled, job.storage
ORDER BY job.schedule
```

### Find VMs not covered by any backup job
```cypher
MATCH (vm:ProxmoxVM)
WHERE NOT (vm)<-[:BACKS_UP]-(:ProxmoxBackupJob)
AND vm.template = false
RETURN vm.name, vm.node, vm.status
ORDER BY vm.name
```

### Find disabled backup jobs
```cypher
MATCH (job:ProxmoxBackupJob)
WHERE job.enabled = false
RETURN job.id, job.schedule, job.notes
```

### Find VMs protected by HA
```cypher
MATCH (vm:ProxmoxVM)<-[:PROTECTS]-(ha:ProxmoxHAResource)
RETURN vm.name, vm.status, ha.state, ha.group
ORDER BY vm.name
```

### Find HA group configuration
```cypher
MATCH (group:ProxmoxHAGroup)
RETURN group.group, group.nodes, group.restricted, group.nofailback
ORDER BY group.group
```

### Find VMs not protected by HA but should be
```cypher
MATCH (vm:ProxmoxVM)
WHERE vm.template = false
AND vm.status = 'running'
AND NOT (vm)<-[:PROTECTS]-(:ProxmoxHAResource)
RETURN vm.name, vm.node, vm.memory
ORDER BY vm.memory DESC
```

### Find all users and their group memberships
```cypher
MATCH (u:ProxmoxUser)
OPTIONAL MATCH (u)-[:MEMBER_OF_GROUP]->(g:ProxmoxGroup)
RETURN u.userid, u.email, collect(g.groupid) as groups
ORDER BY u.userid
```

### Find users with administrative privileges
```cypher
MATCH (acl:ProxmoxACL)-[:APPLIES_TO_USER]->(u:ProxmoxUser)
MATCH (acl)-[:GRANTS_ROLE]->(r:ProxmoxRole)
WHERE r.roleid = 'Administrator' OR 'Sys.Modify' IN r.privs
RETURN DISTINCT u.userid, u.email, acl.path, r.roleid
ORDER BY u.userid
```

### Find overly permissive ACL entries
```cypher
MATCH (acl:ProxmoxACL)-[:GRANTS_ROLE]->(r:ProxmoxRole)
WHERE acl.path = '/' AND r.roleid = 'Administrator'
MATCH (acl)-[:APPLIES_TO_USER]->(u:ProxmoxUser)
RETURN u.userid, u.email, r.roleid, acl.path
```

### Find firewall rules allowing all traffic
```cypher
MATCH (rule:ProxmoxFirewallRule)
WHERE rule.action = 'ACCEPT'
AND rule.source IS NULL
AND rule.dest IS NULL
RETURN rule.scope, rule.scope_id, rule.pos, rule.comment
ORDER BY rule.scope, rule.pos
```

### Find open ports in firewall rules
```cypher
MATCH (rule:ProxmoxFirewallRule)
WHERE rule.action = 'ACCEPT' AND rule.enable = true
AND rule.dport IS NOT NULL
RETURN DISTINCT rule.dport, count(rule) as rule_count,
       collect(DISTINCT rule.scope) as scopes
ORDER BY rule_count DESC
```

### Find overly permissive firewall rules using IPSets
```cypher
MATCH (rule:ProxmoxFirewallRule)-[:USES_IPSET]->(ipset:ProxmoxFirewallIPSet)
WHERE rule.action = 'ACCEPT'
  AND '0.0.0.0/0' IN ipset.cidrs
RETURN rule.id, rule.scope, rule.dport, ipset.name, ipset.cidrs
ORDER BY rule.scope
```

### Find firewall rules that depend on a specific IPSet
```cypher
MATCH (rule:ProxmoxFirewallRule)-[r:USES_IPSET]->(ipset:ProxmoxFirewallIPSet {name: 'trusted_networks'})
RETURN rule.id, rule.action, rule.dport,
       r.in_source as used_in_source,
       r.in_dest as used_in_dest
```

### Find SSL certificates expiring soon (using computed property)
```cypher
MATCH (cert:ProxmoxCertificate)
WHERE cert.expires_soon = true
RETURN cert.node_name, cert.subject, cert.expires_in_days, cert.fingerprint
ORDER BY cert.expires_in_days
```

### Find all expired certificates
```cypher
MATCH (cert:ProxmoxCertificate)
WHERE cert.is_expired = true
RETURN cert.node_name, cert.subject, cert.expires_in_days, cert.fingerprint
```

### Certificate expiration dashboard
```cypher
MATCH (n:ProxmoxNode)-[:HAS_CERTIFICATE]->(cert:ProxmoxCertificate)
RETURN n.name, cert.subject,
       cert.expires_in_days,
       CASE
         WHEN cert.is_expired THEN 'EXPIRED'
         WHEN cert.expires_soon THEN 'EXPIRING SOON'
         ELSE 'OK'
       END as status
ORDER BY cert.expires_in_days
```

### Access control audit: Find users without recent activity
```cypher
MATCH (u:ProxmoxUser)
WHERE u.enable = true
OPTIONAL MATCH (acl:ProxmoxACL)-[:APPLIES_TO_USER]->(u)
RETURN u.userid, u.email, u.expire, count(acl) as permission_count
ORDER BY permission_count DESC
```

### Find all users who can access a specific VM (using HAS_PERMISSION)
```cypher
MATCH (u:ProxmoxUser)-[p:HAS_PERMISSION]->(vm:ProxmoxVM {name: 'production-db'})
RETURN u.userid, u.email, p.role, p.privileges, p.via_group
ORDER BY u.userid
```

### Find what resources a user can access
```cypher
MATCH (u:ProxmoxUser {userid: 'admin@pam'})-[p:HAS_PERMISSION]->(resource)
RETURN labels(resource)[0] as resource_type,
       resource.id as resource_id,
       p.role,
       p.privileges,
       p.via_group as inherited_from_group
ORDER BY resource_type, resource_id
```

### Find users with cluster-wide admin access
```cypher
MATCH (u:ProxmoxUser)-[p:HAS_PERMISSION]->(c:ProxmoxCluster)
WHERE 'Sys.Modify' IN p.privileges OR p.role = 'Administrator'
RETURN u.userid, u.email, p.role, p.via_group
ORDER BY u.userid
```

### Find VMs accessible by a specific group
```cypher
MATCH (g:ProxmoxGroup {groupid: 'developers'})-[p:HAS_PERMISSION]->(vm:ProxmoxVM)
RETURN vm.name, vm.status, p.role, p.privileges
ORDER BY vm.name
```

### Audit: Find users with permissions inherited through groups
```cypher
MATCH (u:ProxmoxUser)-[p:HAS_PERMISSION]->(resource)
WHERE p.via_group = true
RETURN u.userid, labels(resource)[0] as resource_type,
       resource.id as resource_id, p.role
ORDER BY u.userid, resource_type
```

### Complete permission path: trace ACL to user to resource
```cypher
MATCH path = (u:ProxmoxUser)<-[:APPLIES_TO_USER]-(acl:ProxmoxACL)
             -[:GRANTS_ROLE]->(role:ProxmoxRole)
MATCH (acl)-[:GRANTS_ACCESS_TO]->(resource)
WHERE u.userid = 'developer@pve'
RETURN u.userid, acl.path, role.roleid, role.privs,
       labels(resource)[0] as resource_type, resource.id
```

## Permissions Required

The Proxmox user or API token needs the following permissions:

- **VM.Audit**: Read VM configurations
- **Datastore.Audit**: Read storage information
- **Sys.Audit**: Read system information

The built-in `PVEAuditor` role provides all necessary permissions.

## SSL Verification

By default, SSL certificates are verified. To disable verification (not recommended for production):

```bash
cartography --proxmox-host proxmox.example.com \
    --proxmox-verify-ssl false
```

## Architecture

The Proxmox integration follows Cartography's **modern data model approach** with the standard **Get → Transform → Load → Cleanup** pattern:

1. **Get**: Retrieve data from Proxmox API using proxmoxer library
2. **Transform**: Convert API responses to standardized format
3. **Load**: Store data in Neo4j using modern `load()` function with schema definitions
4. **Cleanup**: Remove stale data using `GraphJob.from_node_schema()`

### Modern Data Model Benefits

The Proxmox module uses Cartography's **declarative data model schemas** instead of handwritten Cypher queries:

- **Type Safety**: Python dataclasses provide compile-time validation
- **Maintainability**: Schema definitions are centralized in `cartography/models/proxmox/`
- **Automatic Cleanup**: GraphJob handles stale data removal automatically
- **Relationship Management**: Declarative relationship schemas simplify connections
- **Indexing**: Extra indexes created automatically on frequently queried fields

Each module (`cluster.py`, `compute.py`, `storage.py`) follows this pattern independently.

## Development

### Running Tests

```bash
pytest tests/unit/cartography/intel/proxmox/
pytest tests/integration/cartography/intel/proxmox/
```

### Adding New Resources

To add new Proxmox resources following modern patterns:

1. **Define Data Model** in `cartography/models/proxmox/`:
   - Create node properties class extending `CartographyNodeProperties`
   - Define relationship schemas extending `CartographyRelSchema`
   - Create node schema extending `CartographyNodeSchema`

2. **Implement Intel Module** in `cartography/intel/proxmox/`:
   - Create `get()` functions for API calls
   - Create `transform()` functions for data shaping
   - Create `load()` functions using modern `load()` with schemas
   - Create `sync()` orchestration function

3. **Update Main Entry Point** in `__init__.py`:
   - Call your sync function
   - Add cleanup using `GraphJob.from_node_schema()`

4. **Add Tests**:
   - Unit tests for transform functions
   - Integration tests using `check_nodes()` and `check_rels()`

See `AGENTS.md` in the repository root for comprehensive development guidance.

## Troubleshooting

### Connection Issues

If you see connection errors:

1. Verify Proxmox host is reachable
2. Check firewall rules allow port 8006
3. Verify API token/credentials are correct
4. Try disabling SSL verification temporarily

### Permission Errors

If you see 403 errors:

1. Verify token/user has appropriate roles
2. Check ACL permissions on `/` path
3. Ensure token is not expired

### Import Errors

If proxmoxer is not found:

```bash
pip install proxmoxer>=2.0.1
```

## References

- [Proxmox VE API Documentation](https://pve.proxmox.com/pve-docs/api-viewer/)
- [proxmoxer Library](https://pypi.org/project/proxmoxer/)
- [Cartography Developer Guide](https://cartography-cncf.github.io/cartography/dev/developer-guide.html)
