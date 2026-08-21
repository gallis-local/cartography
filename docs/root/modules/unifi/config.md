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
- To sync multiple sites, run Cartography once per site with a different `--unifi-site` value.

## Troubleshooting

- **`UniFi admin listing failed with unexpected API error ... 404 Not Found`**: The `/rest/admin` endpoint isn't available on every controller version/deployment. This is handled gracefully — the sync logs a warning and skips admin ingestion for that run rather than failing. All other UniFi object types are unaffected.
- **`UniFi admin listing requires super-admin ... privileges`**: The configured account lacks System Admin rights. Grant super-admin access if you need `UnifiAdmin` nodes, or ignore the warning if you don't.
