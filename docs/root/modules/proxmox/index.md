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

After ingestion, typed analysis jobs under
`cartography/analysis/proxmox/analysis.py` derive additional findings: backup
coverage, replication, HA, certificate expiry, guest-agent presence, and
storage/security posture, plus linking into the shared ontology.

Each job is scoped to one cluster and clears the properties it sets before
re-evaluating them, so a finding stops being reported once its condition no
longer holds. Two consequences worth knowing:

- A finding property is **absent** rather than `false` when it does not apply.
  Query `WHERE n.backup_risk` or `WHERE n.backup_risk IS NOT NULL`, not
  `WHERE n.backup_risk = false`.
- Findings that only make sense when a feature is configured (`ha_risk`,
  `replication_risk`) stay silent on clusters that do not use HA or
  replication, and on standalone nodes where HA is not possible.

Effective permissions (`HAS_PERMISSION`) and role assignment (`HAS_ROLE`) are
not analysis jobs: they are derived at ingestion time in
`cartography/intel/proxmox/access.py` and loaded as MatchLinks, so they get
cluster-scoped stale-edge cleanup.

## Resilience

Proxmox is treated as a system that can be partially unreachable, and
best-effort mode is **on by default**: a failing submodule (SDN disabled on this
cluster, HA absent, a read-only token that cannot enumerate API tokens) is logged
with its reason and skipped rather than aborting the whole sync. Pass
`--no-proxmox-best-effort-mode` to fail fast instead.

Individual fetches deliberately do not swallow errors. A fetch of a whole
collection lets the error propagate to that best-effort boundary; only fetches
issued once per guest, node or user catch and continue, so one refusal does not
cost the other items. Permission denials are reported as such, and say the data
will be absent rather than empty.

`--proxmox-max-retries`/`--proxmox-retry-backoff` control retry-with-backoff for
transient API failures.

```{toctree}
config
schema
```
