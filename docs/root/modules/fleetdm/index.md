# FleetDM

[Fleet](https://fleetdm.com/) is an open-source device management (MDM) and
osquery fleet manager. This module ingests Fleet's inventory of enrolled
hosts, the software and vulnerabilities detected on them, and the policies
used to check host compliance.

## Ingested resources

- `FleetDMTenant` - the root node representing the Fleet instance being
  synced.
- `FleetDMFleet` - a Fleet "team": a named grouping of hosts, policies, and
  users.
- `FleetDMHost` - an osquery-enrolled device, labeled as a `Device` in the
  cross-provider ontology.
- `FleetDMSoftware` / `FleetDMSoftwareVersion` - software inventoried across
  hosts, aggregated by title and by specific version.
- `FleetDMVulnerability` - a CVE affecting a software version, labeled as a
  `Finding` and `Risk` in the shared graph interfaces.
- `FleetDMPolicy` - an osquery-based compliance check.
- `FleetDMLabel` - a static or dynamic host grouping.
- `FleetDMUser` - a Fleet console user account, labeled as a `UserAccount`
  and linked to its canonical `Human` identity by email when one exists.

## Key relationships

- `(:FleetDMHost)-[:HAS_SOFTWARE]->(:FleetDMSoftwareVersion)`
- `(:FleetDMHost)-[:MEMBER_OF_LABEL]->(:FleetDMLabel)`
- `(:FleetDMHost)-[:PART_OF_FLEET]->(:FleetDMFleet)`
- `(:FleetDMHost)-[:CHECKS]->(:FleetDMPolicy)` - records whether the host is
  passing or failing each policy.
- `(:FleetDMVulnerability)-[:AFFECTS]->(:FleetDMSoftwareVersion)`
- `(:FleetDMVulnerability)-[:LINKED_TO]->(:CVE)`

```{toctree}
config
schema
```
