# OpenVAS Configuration

Follow these steps to ingest Greenbone Vulnerability Management (GVM/OpenVAS) scan data with Cartography.

## Prerequisites

A running GVM/OpenVAS instance with the `gvmd` daemon reachable over GMP (Greenbone Management Protocol), either directly or via an SSH tunnel.

## Authentication

Create or use an existing GVM user with read access to the tasks, targets, results, and assets you want to sync, and populate an environment variable with the password:

```bash
export GVM_PASSWORD=your_password
```

## Required Permissions

| Parameter | Description |
|-----------|-------------|
| `--openvas-host` | Hostname or IP of the GVM daemon (`gvmd`) GMP endpoint. Defaults to `127.0.0.1`. |
| `--openvas-user` | GVM user for GMP authentication (and SSH login when `--openvas-ssh` is set). Defaults to `admin`. |
| `--openvas-password-env-var` | Environment variable name containing the GVM password. Defaults to `GVM_PASSWORD`. |

## Configure Cartography

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--openvas-port` | `9390` | TCP port of the GVM daemon GMP endpoint. |
| `--openvas-socket-path` | unset | Path to the `gvmd` Unix socket (e.g. `/run/gvmd/gvmd.sock`). Overrides `--openvas-host`/`--openvas-port` when set. |
| `--openvas-tls` | `False` | Connect over TLS instead of plain TCP (port 9391 when `gvmd` TLS is enabled). |
| `--openvas-tls-cafile` | system CA bundle | CA certificate file used to verify the GVM TLS endpoint. |
| `--openvas-ssh` | `False` | Tunnel GMP over SSH instead of plain TCP or TLS, using `--openvas-user`/`--openvas-password` for the SSH login. |
| `--openvas-instance-id` | `host:port` or socket path | Identifier used to scope all OpenVAS nodes in the graph (the `OpenVASInstance` node id). |
| `--openvas-findings-lookback-days` | `180` | Days to look back for results on each run. Stale results outside this window are removed by the cleanup job. |

## Run Cartography

```bash
cartography \
  --openvas-host <gvmd-host-or-ip> \
  --openvas-user admin \
  --openvas-password-env-var GVM_PASSWORD
```

To use a Unix socket instead of TCP:

```bash
cartography \
  --openvas-socket-path /run/gvmd/gvmd.sock \
  --openvas-user admin \
  --openvas-password-env-var GVM_PASSWORD
```

## Troubleshooting

- **Credentials sent unencrypted**: By default the module connects to the GMP endpoint over plain TCP, which sends your GVM credentials unencrypted on the wire. Set `--openvas-tls` (GMP over TLS) or `--openvas-socket-path`/`--openvas-ssh` (no network hop at all) for any deployment where `gvmd` isn't reachable only over a trusted loopback or local socket. The sync logs a warning on every run when connecting over plain TCP without one of these set.
- **Large result sets**: A busy GVM instance can accumulate a very large number of `OpenVASResult` nodes. Tune `--openvas-findings-lookback-days` down if sync time or graph size becomes a concern.
