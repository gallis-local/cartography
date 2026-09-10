# Prowler

```{toctree}
config
schema
```

Cartography ingests Prowler providers, scans, cloud resources, security
findings, and per-framework compliance posture from Prowler Cloud or a
self-hosted Prowler App.

The module creates `ProwlerTenant` (which carries the `Tenant` ontology label),
`ProwlerProvider`, `ProwlerScan`, `ProwlerResource`, `ProwlerComplianceAssessment`,
and `ProwlerFinding` nodes.

The module reads the `/api/v1/findings/latest` and `/api/v1/resources/latest`
endpoints, so the graph reflects the current state of the most recent scan per
provider rather than historical findings.

## Graph shape

`ProwlerTenant` owns every node the module creates through a `RESOURCE` edge,
which is also the cleanup scope. The remaining edges describe how Prowler's own
objects relate:

```
(:ProwlerTenant)-[:RESOURCE]->(:ProwlerProvider | :ProwlerScan | :ProwlerResource | :ProwlerFinding | :ProwlerComplianceAssessment)
(:ProwlerProvider)-[:CONTAINS]->(:ProwlerResource)
(:ProwlerScan)-[:SCANNED]->(:ProwlerProvider)
(:ProwlerScan)-[:IDENTIFIED]->(:ProwlerFinding)
(:ProwlerFinding)-[:AFFECTS]->(:ProwlerResource)
(:ProwlerComplianceAssessment)-[:ASSESSES]->(:ProwlerProvider)
```

A finding can be raised against more than one resource, so `AFFECTS` is
one-to-many.

## Correlation with your cloud inventory

Prowler data is joined to nodes from Cartography's own cloud modules at two
levels. Both are best-effort: an edge appears only when the matching node is
already in the graph, so this module can be synced on its own.

**Account level.** Each `ProwlerProvider` attaches to the cloud tenant it
scans:

```
(:ProwlerProvider)-[:SCANS]->(:AWSAccount | :AzureSubscription | :GCPProject | :KubernetesCluster | :GitHubOrganization)
```

**Resource level.** For AWS providers, `ProwlerResource.uid` is the resource's
ARN, so the resource is joined to the real node by ARN:

```
(:ProwlerResource)-[:REPRESENTS]->(:AWSS3Bucket | :AWSEC2Instance | :AWSRole | ...)
```

This is what makes findings reachable from the assets they are about:

```cypher
MATCH (b:AWSS3Bucket)<-[:REPRESENTS]-(:ProwlerResource)<-[:AFFECTS]-(f:ProwlerFinding)
WHERE f.status = 'FAIL' AND f.severity IN ['critical', 'high']
RETURN b.name, f.check_title, f.severity
```

The generated schema page lists every target label. Two limitations are worth
knowing:

- Only labels whose `arn` property is indexed are joined, so the correlation is
  an index seek rather than a graph scan. A handful of common Prowler check
  targets — `AWSVpc`, `AWSEC2Subnet`, `AWSEC2SecurityGroup`, classic
  `AWSLoadBalancer`, `AWSAPIGatewayRestAPI` — carry no ARN in Cartography at
  all and therefore cannot be joined yet; their findings remain reachable
  through the provider's account-level `SCANS` edge.
- Cartography synthesizes the ARN for S3 buckets and EC2 instances with a
  hardcoded `aws` partition, so those two types do not correlate in GovCloud or
  China partitions. Types whose ARN comes straight from the AWS API are
  unaffected.

## Findings and the SecurityIssue ontology label

Prowler reports passing and manual checks through the same API as failing ones,
so `ProwlerFinding` nodes exist for all three outcomes. Only findings with
`status = 'FAIL'` carry the `SecurityIssue` ontology label, so cross-provider
queries over `:SecurityIssue` do not count passing checks as open issues. Filter
on `status` when querying `ProwlerFinding` directly.

`ProwlerFinding.cve_ids` is populated only when a check's metadata explicitly
names a CVE, which is rare — Prowler checks are configuration checks. These
findings are not linked to `CVEMetadata`, so no EPSS or NVD enrichment is
applied to them; use the `cve` and `cve_metadata` modules for
vulnerability data.

## Compliance posture

Each `ProwlerComplianceAssessment` records how one provider scored against one
compliance framework (CIS, SOC 2, ISO 27001, PCI DSS, HIPAA and others) in its
most recent completed scan, as counts of passed, failed, and manual
requirements. `requirements_manual` is not a failure: those are controls Prowler
cannot evaluate automatically and that need review out-of-band.

```cypher
MATCH (a:ProwlerComplianceAssessment)-[:ASSESSES]->(:ProwlerProvider)-[:SCANS]->(acct:AWSAccount)
WHERE a.requirements_failed > 0
RETURN acct.id, a.framework, a.version, a.requirements_failed, a.total_requirements
ORDER BY a.requirements_failed DESC
```

Findings also carry a `compliance_frameworks` list naming the frameworks each
individual check maps to.
