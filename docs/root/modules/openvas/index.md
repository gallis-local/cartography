# OpenVAS

[OpenVAS](https://www.openvas.org/) (Open Vulnerability Assessment Scanner), delivered as part of the
[Greenbone Vulnerability Management (GVM)](https://www.greenbone.net/) stack, is an open-source vulnerability
scanner. This module connects to a GVM instance's `gvmd` daemon over GMP (Greenbone Management Protocol) and
ingests the scanner's configuration, scan results, and discovered assets into the graph.

## Ingested objects

- **OpenVASInstance** — the root node scoping a single GVM instance. All other OpenVAS nodes hang off it via
  `RESOURCE` edges.
- **OpenVASTask** — a scan task (the definition of a recurring or one-off scan), linked to the `OpenVASTarget`,
  `OpenVASConfig`, and `OpenVASSchedule` it uses.
- **OpenVASTarget** — the set of hosts, ports, and credentials a task scans.
- **OpenVASConfig** — a scan config (the NVT families/preferences a task scans with).
- **OpenVASSchedule** — a recurrence rule that triggers a task automatically.
- **OpenVASCredential** — an SSH/SMB/ESXi/SNMP credential used for authenticated scanning.
- **OpenVASPortList** — a set of ports/port ranges a target is scoped to.
- **OpenVASHost** — a host asset from GVM's asset management, carrying its latest scan severity. Also labeled
  `DeviceInstance` under the cross-provider ontology.
- **OpenVASResult** — an individual vulnerability finding, linking the affected `OpenVASHost`, the `OpenVASNVT`
  that detected it, and the `OpenVASTask` run that produced it. Findings with an associated CVE also carry the
  `CVE` ontology label and connect into Cartography's shared CVE nodes.
- **OpenVASNVT** — a Network Vulnerability Test (an individual scanner check), including its CVSS scoring and
  any CVEs it tests for.
- **OpenVASTLSCertificate** — a TLS certificate discovered via GVM's TLS certificate asset scanning. Also
  labeled `Certificate` under the cross-provider ontology.

## Architecture

Ingestion follows the standard sync = get → transform → load → cleanup pattern per resource type
(`cartography/intel/openvas/`), backed by declarative `CartographyNodeSchema`/`CartographyRelSchema` models
(`cartography/models/openvas/`). All nodes are scoped to a single `OpenVASInstance` (identified by
`--openvas-instance-id`, defaulting to `host:port` or the configured socket path), so cleanup only ever removes
stale data belonging to that instance.

See [Configuration](config.md) for connection and authentication setup.
