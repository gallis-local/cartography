# Harbor Configuration

Configure the URL of a Harbor instance and a credential that can read its projects,
repositories, artifacts, and scan results.

## Prerequisites

- Harbor 2.x. SBOM ingestion needs 2.11 or later.
- A scanner (for example Trivy) enabled in Harbor, with scan-on-push or manual scans
  producing the vulnerability reports and SBOMs Cartography reads.

## Authentication

Cartography authenticates with HTTP basic auth. Use a
[robot account](https://goharbor.io/docs/main/working-with-projects/project-configuration/create-robot-accounts/)
rather than a personal account, and supply the secret through an environment
variable.

Create either a system-level robot account that covers every project, or a
project-level robot account per project. The module syncs the projects the
credential can list, so a project-level robot only inventories its own project.

## Required Permissions

| Resource | Action | Used for |
| --- | --- | --- |
| `project` | `list` | Listing projects |
| `repository` | `list` | Listing repositories |
| `artifact` | `list` | Listing images, tags, and scan summaries |
| `scan` | `read` | Reading vulnerability reports |
| `sbom` | `read` | Reading SBOMs (Harbor 2.11+) |

All of these are read-only. The module only issues `GET` requests.

## Configure Cartography

| Option | Value |
| --- | --- |
| `--harbor-url` | Base https URL of the instance, e.g. `https://harbor.example.com`. No path, query, or fragment. |
| `--harbor-username` | Robot account name, e.g. `robot$cartography`. |
| `--harbor-password-env-var` | Name of the environment variable holding the robot secret, e.g. `HARBOR_PASSWORD`. |
| `--no-harbor-verify-ssl` | Optional. Disables TLS verification for instances whose certificate is not in the trust store. Verification is on by default. |
| `--selected-modules` | Include `harbor`. |

If the URL, username, or password is missing, the module logs that it is
unconfigured and skips ingestion. Plain `http://` URLs are rejected so the
credential is never sent in clear text.

## Run Cartography

```bash
export HARBOR_PASSWORD='your-robot-secret'
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules harbor \
  --harbor-url https://harbor.example.com \
  --harbor-username 'robot$cartography' \
  --harbor-password-env-var HARBOR_PASSWORD
```

Quote the username in a shell: robot account names contain a `$`.

## Troubleshooting

- `401`: Check the robot account name (including the `robot$` prefix) and secret.
- `403` on scan or SBOM endpoints: Add the `scan` and `sbom` read permissions to the
  robot account.
- No vulnerabilities or packages appear: Check `scan_status` and `sbom_status` on the
  `HarborImage` nodes. Images show `null` until Harbor has scanned them.

## References

- [Harbor documentation](https://goharbor.io/docs/)
- [Robot accounts](https://goharbor.io/docs/main/working-with-projects/project-configuration/create-robot-accounts/)
- [Vulnerability scanning](https://goharbor.io/docs/main/administration/vulnerability-scanning/)
- [SBOM generation](https://goharbor.io/docs/main/working-with-projects/working-with-images/sbom-integration/)
