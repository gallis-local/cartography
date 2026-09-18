# UniFi Configuration

Follow these steps to analyze UniFi network objects with Cartography.

## Prerequisites

Ensure you have a UniFi Network Application or UniFi OS console running (self-hosted or cloud).

## Authentication

Create or use an existing local admin account with read access to the site you want to sync, and populate environment variables with your credentials:

```bash
export UNIFI_USER=admin
export UNIFI_PASSWORD=your_password
```

## Required Permissions

| Parameter | Description |
|-----------|-------------|
| `--unifi-host` | IP address or hostname of the UniFi controller |
| `--unifi-user` or `--unifi-user-env-var` | Username (or env var name) for authentication |
| `--unifi-password-env-var` | Environment variable name containing the password |

## Optional Permissions

Granting the sync account **super-admin (System Admin)** privileges additionally enables syncing UniFi admin accounts (`/rest/admin`). Without it, admin listing is skipped gracefully (see Troubleshooting below) and every other object type still syncs normally.

## Configure Cartography

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--unifi-site` | `default` | UniFi site name to sync |
| `--unifi-sites` | _unset_ | UniFi site names to sync (repeatable, overrides `--unifi-site`) |
| `--unifi-port` | `443` | Controller HTTPS port |
| `--unifi-verify-ssl` | `False` | Verify SSL certificate (disable for self-signed certs) |

## Run Cartography

```bash
cartography \
  --unifi-host <controller-ip-or-hostname> \
  --unifi-user-env-var UNIFI_USER \
  --unifi-password-env-var UNIFI_PASSWORD \
  --unifi-site default
```

Alternatively, you can pass the username directly via `--unifi-user`:

```bash
cartography \
  --unifi-host <controller-ip-or-hostname> \
  --unifi-user admin \
  --unifi-password-env-var UNIFI_PASSWORD \
  --unifi-site default
```

## Advanced Configuration

- The default port is `443`, which is used by UniFi OS devices (UDM, UDM-Pro, UDM-SE) and cloud controllers. For legacy self-hosted UniFi Network Applications, use `--unifi-port 8443`.
- Many self-hosted UniFi controllers use self-signed TLS certificates. Set `--unifi-verify-ssl False` (the default) to allow connections to such controllers.
- The module requires `aiounifi>=81` and Python 3.12+.
- To sync several sites in one run, repeat `--unifi-sites`: `--unifi-sites default --unifi-sites branch-office`. Each site is synced and analyzed independently under a shared update tag.

## Node Identity and Multi-Site Deployments

`UnifiClient` and `UnifiDevice` are keyed on `"{site_id}_{mac}"`, not on the bare MAC.
MAC addresses are only unique within a single controller, so a bare-MAC key made the same
physical machine seen by two controllers collapse onto one node that carried `RESOURCE`
edges from both sites and a `site_id` that changed depending on which sync ran last. The
raw MAC is still available on the `mac` property.

Every relationship that resolves a client or device (`CONNECTED_TO_AP`,
`CONNECTED_TO_SWITCH`, `UPLINKED_TO_SWITCH`, `CONNECTED_TO_GATEWAY`, `UPLINK_TO`,
`HAS_PORT`, `HAS_OUTLET`, `MEASURED_BY`, `APPLIES_TO_CLIENT`) matches on the site-scoped
id. `UnifiPort` and `UnifiOutlet` remain keyed on `"{device_mac}_{index}"`.

```{note}
This is a breaking change to the graph schema. Nodes ingested by an earlier version keep
their bare-MAC ids and will not be updated or cleaned up by later syncs, because cleanup
only reaches nodes attached to the site being synced. Purge them once, deliberately, using
the query in the Troubleshooting section below.
```

## Analysis Jobs

After ingestion the module runs seven typed analysis jobs, each scoped to the site being
synced. Every job removes the properties it owns before recomputing them, so a flag never
outlives the condition that set it, and a finding is never carried over from another site.

| Job | Sets |
|-----|------|
| `unifi_internet_exposure` | `exposed_internet`, `exposed_internet_type` on `UnifiDevice`, `UnifiWlan`, `UnifiPortForward` |
| `unifi_firmware_compliance` | `firmware_compliant`, `firmware_version_current`, `firmware_version_latest` on `UnifiDevice` |
| `unifi_guest_isolation` | `guest_isolated`, `guest_isolation_issues` on `UnifiWlan` and `UnifiClient`; `guest_networks` on `UnifiVoucher` |
| `unifi_device_health` | `health_score`, `health_issues`, `temperature_status`, `power_status` on `UnifiDevice` |
| `unifi_network_config_audit` | `audit_score`, `audit_issues`, `audit_tier` on `UnifiNetworkConfig` |
| `unifi_power_monitoring` | `power_status`, `power_issues` on `UnifiOutlet` |
| `unifi_wan_performance` | `performance_score`, `performance_issues`, `performance_tier` on `UnifiSpeedtest` |

Notes on interpreting the results:

- `firmware_compliant` is set only when the controller positively reports the device's
  upgrade state. A device whose state is unknown is left unflagged rather than defaulted
  to compliant.
- `performance_score` is absent, and `performance_tier` is `unknown`, for a speedtest that
  did not return all three of download, upload and ping. A missing measurement is not
  scored as a good one.
- Power, voltage, current and power-factor readings are stored as numbers. The controller
  reports them as decimal strings; the module coerces them, and an absent or unparseable
  reading becomes null rather than a sentinel value.
- `guest_isolation_issues` and the other `*_issues` properties are always lists.

## Troubleshooting

- **`UniFi admin listing failed with unexpected API error ... 404 Not Found`**: The `/rest/admin` endpoint isn't available on every controller version/deployment. This is handled gracefully — the sync logs a warning and skips admin ingestion for that run rather than failing. All other UniFi object types are unaffected.
- **Duplicate `UnifiClient`/`UnifiDevice` nodes after upgrading**: nodes created before
  the site-scoped id change keep their bare-MAC ids. Find them with the read-only query
  below, confirm the list, then purge them.

  ```cypher
  MATCH (n)
  WHERE (n:UnifiClient OR n:UnifiDevice)
    AND NOT n.id STARTS WITH n.site_id + '_'
  RETURN labels(n) AS labels, n.id AS id, n.site_id AS site_id,
         n.mac AS mac, n.lastupdated AS lastupdated
  ORDER BY labels, id
  ```

- **`UniFi admin listing requires super-admin ... privileges`**: The configured account lacks System Admin rights. Grant super-admin access if you need `UnifiAdmin` nodes, or ignore the warning if you don't.
