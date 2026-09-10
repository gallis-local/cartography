# Prowler Configuration

Configure the Prowler API origin and a read-only credential for the tenant you
want in the graph.

## Authentication

Cartography authenticates to Prowler Cloud or a self-hosted Prowler App with
either an API key or a user email and password. Use an API key when possible.

### API key (recommended)

Create an API key in the Prowler UI, or with `POST /api/v1/api-keys`. The
plaintext key is shown only once, at creation time, so store it immediately.
API keys have a default lifetime of 365 days.

Supply the key to Cartography in the `PROWLER_API_KEY` environment variable.

### Email and password (JWT)

Email and password authentication is used only when no API key is configured.
Cartography exchanges the credentials at `POST /api/v1/tokens` for a short-lived
access token (30 minutes) and refreshes it automatically during the sync.

Pass the email with `--prowler-email`, and supply the password in the
`PROWLER_PASSWORD` environment variable.

API key authentication is preferred for unattended runs.

## Required Permissions

The credential needs read access to the tenant's providers, scans, resources,
and findings. In Prowler's RBAC, that is any role with `unlimited_visibility`,
or a role whose provider groups cover the accounts you want in the graph.

A viewer-level role is sufficient: Cartography only issues `GET` requests.

## Configure Cartography

| Option | Default | Required | Description |
|--------|---------|----------|-------------|
| `--prowler-api-url` |  | Yes | Base URL of the Prowler API, e.g. `https://api.prowler.com` for Prowler Cloud or the origin of a self-hosted Prowler App API. |
| `--prowler-api-key-env-var` | `PROWLER_API_KEY` | No | Environment variable that contains the Prowler API key. |
| `--prowler-email` |  | No | Prowler user email. Only used for JWT authentication when no API key is configured. |
| `--prowler-password-env-var` | `PROWLER_PASSWORD` | No | Environment variable that contains the Prowler user password. |
| `--prowler-tenant-id` |  | No | Prowler tenant UUID to sync. Defaults to the tenant of the credential's first membership. |

## Run Cartography

Against Prowler Cloud:

```bash
export PROWLER_API_KEY="..."

cartography \
  --selected-modules prowler \
  --prowler-api-url https://api.prowler.com
```

Against a self-hosted Prowler App:

```bash
export PROWLER_API_KEY="..."

cartography \
  --selected-modules prowler \
  --prowler-api-url http://localhost:8080
```

```{note}
Cartography only accepts a plaintext `http://` API URL when it points at
`localhost` or `127.0.0.1`. A remote self-hosted Prowler App must be reached
over `https` so the credential is not sent in the clear.
```

## Advanced Configuration

If your credential has membership in more than one Prowler tenant, set
`--prowler-tenant-id` to the tenant UUID you want to sync. Otherwise Cartography
uses the tenant of the credential's first membership.

## Troubleshooting

- HTTP `401`: The credential is missing or expired, or the `Authorization`
  header never reached the API. Check the key or password, and check that any
  proxy in front of a self-hosted Prowler App forwards the header.
- HTTP `403`: The role lacks visibility of the provider. Grant
  `unlimited_visibility`, or add the provider group to the role.
- HTTP `400`: Usually a malformed tenant id. Check that `--prowler-tenant-id` is
  a valid UUID.

## References

- [Prowler documentation](https://docs.prowler.com)
- [Prowler API reference](https://api.prowler.com/api/v1/docs)
