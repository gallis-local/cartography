# Proxmox Virtual Environment

The Proxmox module syncs a self-hosted [Proxmox VE](https://www.proxmox.com/en/proxmox-virtual-environment)
cluster: its nodes, virtual machines, containers, storage, networking, access
control, and disaster-recovery configuration. It's modeled as a
single-tenant virtualization platform, where the `ProxmoxCluster` is the root
node that every other Proxmox node type hangs off of via a `RESOURCE`
sub-resource relationship.

To sync more than one cluster, run Cartography once per cluster (see
[Advanced Configuration](config.md#advanced-configuration) in the config
page). Each cluster gets its own `ProxmoxCluster` node, and cleanup is scoped
by cluster so syncing one never touches another's data.

## What gets ingested

Organized by domain:

- **Cluster and nodes** — `ProxmoxCluster`, `ProxmoxNode`, per-node network
  interfaces, and per-node status (kernel version, load average, PVE
  version, CPU/swap info) fetched from the node status endpoint.
- **Compute** — `ProxmoxVM` (QEMU) and `ProxmoxContainer` (LXC), their disks
  and network interfaces (dual-stack IPv4/IPv6), and optionally QEMU Guest
  Agent data (hostname, OS info, live network interfaces) when
  `--proxmox-enable-guest-agent` is set.
- **Storage** — `ProxmoxStorage`, labeled as `BlockStorage` or `FileStorage`
  depending on its Proxmox storage type.
- **Snapshots** — VM/container snapshot chains, including parent/child
  relationships.
- **Resource pools** — `ProxmoxPool`, labeled as a `ComputeCluster` in the
  ontology, linked to the VMs and storage it contains.
- **Software-Defined Networking (SDN)** — SDN zones (labeled as
  `VirtualNetwork`), VNets (labeled as `Subnet`), and their scoping to
  specific cluster nodes.
- **Access control** — users, groups, roles, and ACLs, with ontology labels
  (`UserAccount`, `UserGroup`, `PermissionRole`), plus authentication realms
  (labeled `IdentityProvider`) and API tokens (labeled `APIKey`).
- **Firewall** — cluster/node/VM firewall rules and global firewall options.
- **Certificates** — node TLS certificates, labeled `Certificate`.
- **Disaster recovery** — backup jobs, replication jobs, and HA
  groups/resources.

## Ontology integration

Proxmox nodes carry ontology labels so they can be queried alongside the
same resource types from other providers: `UserAccount`, `UserGroup`,
`PermissionRole`, `IdentityProvider`, `ComputeInstance`, `ComputeCluster`,
`Tenant`, `VirtualNetwork`, `Subnet`, `DeviceInstance`, `APIKey`, and
`Certificate`.

## Post-ingestion analysis

After ingestion, several analysis jobs derive additional relationships and
findings: effective-permissions propagation, role assignment
(`HAS_ROLE`) linking, ontology linking, and dedicated jobs for backup
coverage, replication, HA, certificate expiry, guest-agent presence, and
storage/security posture. See [analysis.md](analysis.md) if present, or the
job definitions under `cartography/data/jobs/analysis/proxmox_*.json`, for
the underlying queries.

## Resilience

Proxmox is treated as a system that can be partially unreachable: pass
`--proxmox-best-effort-mode` to have a failing submodule (say, SDN is
disabled on this cluster) log and get skipped rather than aborting the whole
sync, and `--proxmox-max-retries`/`--proxmox-retry-backoff` to control
retry-with-backoff behavior for transient API failures.

```{toctree}
config
schema
```
