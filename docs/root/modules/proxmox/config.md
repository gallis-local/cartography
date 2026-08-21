# Proxmox Configuration

Follow these steps to analyze Proxmox Virtual Environment infrastructure with Cartography.

## Prerequisites

Proxmox VE 7.0+ is required (tested with 8.x). Read-only access is sufficient — the
built-in `PVEAuditor` role is recommended.

## Authentication

Cartography supports two authentication methods against the Proxmox API. Pick one.

### API Token Authentication (Recommended)

1. Create an API token in Proxmox:
    1. Navigate to **Datacenter → Permissions → API Tokens** in the Proxmox web interface.
    1. Click **Add** to create a new token.
    1. Set the user to `root@pam` (or another user with appropriate permissions).
    1. Set the token name to `cartography`.
    1. Uncheck **Privilege Separation** (or grant the `PVEAuditor` role separately).
    1. Click **Add** and save the token value securely.

1. Populate environment variables with the token name and value:

    ```bash
    export PROXMOX_TOKEN_NAME="cartography"
    export PROXMOX_TOKEN_VALUE="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    ```

### Password Authentication

1. Populate an environment variable with the password:

    ```bash
    export PROXMOX_PASSWORD="your-password"
    ```

## Required Permissions

| Permission | Purpose |
| --- | --- |
| `VM.Audit` | Read VM and container configurations |
| `Datastore.Audit` | Read storage information |
| `Sys.Audit` | Read system and node information |

The built-in `PVEAuditor` role grants all of the above and is sufficient for a
full, read-only sync.

## Optional Permissions

Token enumeration (`ProxmoxAPIToken` nodes) requires elevated rights beyond
`PVEAuditor`. If the configured user or token cannot list other users' API
tokens, Cartography logs a debug-level "Could not fetch tokens" message per
user and continues the rest of the sync — this is expected unless you've
granted broader access.

## Configure Cartography

| CLI flag | Environment variable it reads | Purpose |
| --- | --- | --- |
| `--proxmox-host` | — | Proxmox host to sync (e.g., `proxmox.example.com`) |
| `--proxmox-port` | — | API port (default `8006`) |
| `--proxmox-user` | — | Proxmox user, e.g. `root@pam` |
| `--proxmox-token-name-env-var` | Name of the env var holding the token name | Token auth (recommended) |
| `--proxmox-token-value-env-var` | Name of the env var holding the token value | Token auth (recommended) |
| `--proxmox-password-env-var` | Name of the env var holding the password | Password auth (fallback) |
| `--proxmox-verify-ssl` | — | Verify TLS certificates (default `true`) |
| `--proxmox-timeout` | — | API request timeout in seconds (default `30`) |
| `--proxmox-enable-guest-agent` | — | Collect QEMU Guest Agent data (requires the agent installed in VMs) |
| `--proxmox-best-effort-mode` | — | Log and continue past a failing submodule sync instead of aborting the whole Proxmox sync |
| `--proxmox-max-retries` | — | Max retry attempts for transient API failures (connection errors, 5xx, rate limiting) |
| `--proxmox-retry-backoff` | — | Exponential backoff factor between retries |

## Run Cartography

```bash
export PROXMOX_TOKEN_NAME="cartography"
export PROXMOX_TOKEN_VALUE="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

cartography --neo4j-uri bolt://localhost:7687 \
    --proxmox-host proxmox.example.com \
    --proxmox-user root@pam \
    --proxmox-token-name-env-var PROXMOX_TOKEN_NAME \
    --proxmox-token-value-env-var PROXMOX_TOKEN_VALUE
```

## Advanced Configuration

To sync multiple Proxmox clusters, run Cartography separately (with its own
`--proxmox-host` and credentials) once per cluster. Each cluster is
represented as its own `ProxmoxCluster` node in the graph, and cleanup is
scoped per cluster so syncing one cluster never deletes another cluster's
nodes.

## Troubleshooting

If SSL verification fails against a self-signed Proxmox certificate, either
install the certificate in your system trust store or pass
`--proxmox-verify-ssl false` (not recommended for production).
