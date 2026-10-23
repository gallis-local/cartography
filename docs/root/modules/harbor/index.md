# Harbor

The Harbor module ingests the container registry inventory of a
[Harbor](https://goharbor.io/) instance, together with the vulnerability scan
results and software bills of materials (SBOMs) Harbor holds for each image:

- Projects and the repositories inside them.
- Container images and multi-architecture manifest lists, with their tags.
- Vulnerabilities from Harbor's configured scanner (Trivy by default), per image.
- SBOM packages from the SPDX document Harbor generated, per image.

`HarborInstance` contains every other node through `RESOURCE` relationships, so
two Harbor instances can be synced side by side without affecting each other's
cleanup. `HarborProject` connects to its repositories through `HAS_REPOSITORY`,
and `HarborRepository` connects to its images through `HAS_IMAGE`. A tag points
at its image through `IMAGE`, and the repository connects to its tags through
`REPO_IMAGE`. A manifest list points at its platform-specific children through
`CONTAINS_IMAGE`.

Findings connect to the image they were reported on through `AFFECTS`, and to
the SBOM package they concern through `AFFECTS` when the image has an SBOM.
Packages connect to their image through `DEPLOYED`.

## Ontology integration

| Harbor node | Ontology label |
| --- | --- |
| `HarborInstance` | `Tenant` |
| `HarborRepository` | `ContainerRegistry` |
| `HarborImage` | `Image` for single-platform images, `ImageManifestList` for manifest lists |
| `HarborImageTag` | `ImageTag` |
| `HarborVulnerability` | `Risk`, and `CVE` when the scanner reported a CVE identifier |

Package nodes feed the `Package` / `PackageVersion` ontology through their
normalized package identifier, which matches the identifiers Trivy and Syft
produce, so the same package is recognised across scanners.

## Scan data behavior

Harbor scans and generates SBOMs asynchronously, and only when a scanner is
configured and a project or policy has requested it. The module therefore reads
the scan state Harbor reports on every image (`scan_status`, `sbom_status`) and
fetches the vulnerability report or SBOM only for images where that work
completed successfully. Images that were never scanned still appear, with a null
`scan_status`.

- Findings and packages describe the last completed scan at the time of the sync.
  An image that is being rescanned when Cartography runs has no completed scan to
  read, so its findings and packages are removed by that run's cleanup and return
  on the next run after the scan completes.
- Manifest lists are not fetched directly. Harbor aggregates their children's
  findings, so ingesting the children alone avoids duplicates.
- Artifacts that are not container images, such as Helm charts, are skipped.
- SBOM support requires Harbor 2.11 or later. On older releases `sbom_status` stays
  null and no packages are ingested; vulnerabilities are unaffected.

Syncing removes stale nodes only within the configured instance, after the
complete collection for that resource type was fetched. API and pagination
failures propagate without cleaning up the failed collection.

See [configuration](config.md) for setup and [schema](schema.md) for graph fields.

```{toctree}
config
schema
```
