# FleetDM Configuration

Before running this module, you need a running Fleet server and an API token
for a Fleet user with read access to the resources you want to ingest.

## Authentication

Cartography authenticates to Fleet using an API token sent as a Bearer token.

1. Log in to your Fleet server.
2. Generate an API-only user, or copy the API token for an existing user from
   **Settings > My account > Get API token**.
3. Store the token in an environment variable (do not put it directly on the
   command line or in a config file).

## Configure Cartography

| Environment variable | CLI option | Required | Description |
|---|---|---|---|
| Value of `--fleetdm-base-url-env-var` | `--fleetdm-base-url-env-var` | Yes | Base URL of the Fleet server, e.g. `https://fleet.example.com`. |
| Value of `--fleetdm-api-token-env-var` | `--fleetdm-api-token-env-var` | Yes | Fleet API token. |

Both options take the *name* of an environment variable, not the value
itself. Cartography reads the credential from that environment variable at
runtime.

## Run Cartography

```bash
export FLEETDM_BASE_URL=https://fleet.example.com
export FLEETDM_API_TOKEN=your_token

cartography --neo4j-uri <uri> \
    --fleetdm-base-url-env-var FLEETDM_BASE_URL \
    --fleetdm-api-token-env-var FLEETDM_API_TOKEN
```

If either option is omitted, the FleetDM sync is skipped with a log message.

## Fleet Premium

`GET /api/v1/fleet/fleets` is gated behind Fleet Premium. On Fleet Free it
answers 402/403, which the sync logs as a warning and treats as "no fleets",
so `FleetDMFleet` will be empty and no host will have a `PART_OF_FLEET`
relationship. Vulnerability severity metadata (`cvss_score`,
`epss_probability`, `cisa_known_exploit`, `cve_published`,
`resolved_in_version`) and a host's `critical_vulnerabilities_count` are also
Premium-only and stay `null` on Fleet Free.

## References

- [Fleet REST API documentation](https://fleetdm.com/docs/rest-api/rest-api)
