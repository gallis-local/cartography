# Prowler

```{toctree}
config
schema
```

Cartography ingests Prowler providers, scans, cloud resources, and security
findings from Prowler Cloud or a self-hosted Prowler App.

The module creates `ProwlerTenant` (which carries the `Tenant` ontology label),
`ProwlerProvider`, `ProwlerScan`, `ProwlerResource`, and `ProwlerFinding` (which
carries the `SecurityIssue` ontology label) nodes.

Each `ProwlerProvider` is linked to the matching `AWSAccount`,
`AzureSubscription`, `GCPProject`, or `KubernetesCluster` node when that cloud
module has also been synced, so Prowler findings can be traversed from your
existing cloud inventory.

The module reads the `/api/v1/findings/latest` and `/api/v1/resources/latest`
endpoints, so the graph reflects the current state of the most recent scan per
provider rather than historical findings.
