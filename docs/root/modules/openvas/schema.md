# OpenVAS Schema

## Overview

Cartography ingests hosts, scan tasks and vulnerability findings from an [OpenVAS](https://www.greenbone.net/en/)/GVM (Greenbone Vulnerability Management) instance over the GMP protocol (via the `python-gvm` library). The module connects to the gvmd manager daemon — over plain TCP, TLS, a Unix socket, or SSH — and loads the following resources into the graph:

- hosts
- tasks (scans), targets, scan configs and schedules
- port lists and credentials
- scan results (findings) and the NVTs that detected them
- TLS certificates

NVTs are ingested **only as they are referenced by detected results** (deduplicated by OID); the full NVT feed is intentionally not synced, keeping sync time proportional to actual findings.

## Configuration

| CLI flag | Default | Required | Description |
|---|---|---|---|
| `--openvas-host` | `None` | Yes* | Hostname or IP of the gvmd manager (or the SSH host when `--openvas-ssh` is set). |
| `--openvas-port` | `9390` | No | Port of the gvmd manager. |
| `--openvas-user` | `admin` | No | GMP username (or SSH username when `--openvas-ssh` is set). |
| `--openvas-password-env-var` | `GVM_PASSWORD` | Yes | Environment variable holding the GMP (or SSH) password. If unset, the OpenVAS sync is skipped. |
| `--openvas-socket-path` | `None` | No | Path to a gvmd Unix socket. When set, overrides `--openvas-host`/`--openvas-port`. |
| `--openvas-tls` | `False` | No | Connect to gvmd over TLS with certificate verification. |
| `--openvas-tls-cafile` | `None` | No | CA bundle used to verify the gvmd TLS certificate (defaults to system CAs). |
| `--openvas-ssh` | `False` | No | Connect over SSH instead of TCP/TLS. `--openvas-user`/`--openvas-password` are then used for the SSH login. |
| `--openvas-instance-id` | auto | No | Identifier used to scope all graph nodes for this instance. Defaults to `host:port`, or the socket path when `--openvas-socket-path` is set. |
| `--openvas-findings-lookback-days` | `180` | No | Number of days of scan results to retrieve on each sync (filtered on `created`). Stale results outside this window are removed from the graph by the cleanup job. |

\* Unless `--openvas-socket-path` is set.

## Nodes

### OpenVASInstance

Represents the GVM instance being synced — the tenant-like root node. All other OpenVAS nodes are scoped under this node via `RESOURCE` relationships, and cleanup of the module's resources runs through it.

| Field | Description |
|---|---|
| **id** | The instance identifier: `--openvas-instance-id`, else `host:port` (or the socket path) |
| name | Display name (host or `unix:` + socket path) |
| host | gvmd hostname/IP |
| port | gvmd port (string) |
| user | GMP user used for authentication |
| lastupdated | Timestamp of the last sync run |

### OpenVASHost

A host asset tracked by GVM. Carries the cross-provider `DeviceInstance` label, so it matches `(:DeviceInstance)` alongside AWS EC2, Tenable, etc.

| Field | Description |
|---|---|
| **id** | Host UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | Host display name |
| **ip** | Primary IP address (indexed) |
| **hostname** | Hostname (indexed) |
| os | Detected operating system |
| comment | User comment |
| creation_time / modification_time | GVM audit timestamps |
| severity | Host-level severity (e.g. `High`) |
| **asset_id** | GVM asset UUID (indexed) |
| latest_scan_date | Timestamp of the most recent scan |
| latest_scan_task_id / latest_scan_task_name | Task that produced the most recent scan |
| source_type | How the host was discovered (e.g. `manual`) |
| identifiers | List of alternative host identifiers (IPs, hostnames, SNMP community names) |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASHost)
(:OpenVASHost)-[:LAST_SCANNED_BY]->(:OpenVASTask)
(:OpenVASResult)-[:AFFECTS]->(:OpenVASHost)
```

### OpenVASTask

A scan task defined in GVM. Tasks can reference a target, a scan config and a schedule.

| Field | Description |
|---|---|
| **id** | Task UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | Task name |
| comment | User comment |
| status | Task status (e.g. `Done`, `Running`) |
| alterable | Whether the task is alterable |
| creation_time / modification_time | GVM audit timestamps |
| last_report_id | UUID of the most recent report |
| last_report_timestamp | Timestamp of the most recent report |
| last_report_severity | Severity of the most recent report |
| last_report_scan_start / last_report_scan_end | Scan window of the most recent report |
| target_id / target_name | Target this task scans |
| config_id / config_name | Scan config used |
| schedule_id / schedule_name | Schedule that triggers the task (when scheduled) |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASTask)
(:OpenVASTask)-[:SCANS]->(:OpenVASTarget)
(:OpenVASTask)-[:USES]->(:OpenVASConfig)
(:OpenVASTask)-[:USES]->(:OpenVASSchedule)
(:OpenVASHost)-[:LAST_SCANNED_BY]->(:OpenVASTask)
(:OpenVASResult)-[:PART_OF_SCAN]->(:OpenVASTask)
```

### OpenVASTarget

A set of hosts that tasks scan.

| Field | Description |
|---|---|
| **id** | Target UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | Target name |
| comment | User comment |
| creation_time / modification_time | GVM audit timestamps |
| hosts | Hosts covered by the target (IPs, CIDRs, ranges) |
| max_hosts | Maximum number of hosts |
| exclude_hosts | Hosts excluded from the target |
| port_list_id / port_list_name | Port list used |
| alive_test | Alive-test strategy |
| allow_simultaneous_ips | Whether simultaneous IPs are allowed |
| reverse_lookup_only / reverse_lookup_unify | Reverse-lookup settings |
| ssh_credential_id / smb_credential_id / esxi_credential_id / snmp_credential_id | Credentials used for authenticated scanning |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASTarget)
(:OpenVASTask)-[:SCANS]->(:OpenVASTarget)
(:OpenVASTarget)-[:USES]->(:OpenVASPortList)
(:OpenVASTarget)-[:USES_SSH_CREDENTIAL]->(:OpenVASCredential)
(:OpenVASTarget)-[:USES_SMB_CREDENTIAL]->(:OpenVASCredential)
(:OpenVASTarget)-[:USES_ESXI_CREDENTIAL]->(:OpenVASCredential)
(:OpenVASTarget)-[:USES_SNMP_CREDENTIAL]->(:OpenVASCredential)
```

### OpenVASConfig

A scan configuration (family of NVTs and settings) used by tasks.

| Field | Description |
|---|---|
| **id** | Config UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | Config name (e.g. `Full and fast`) |
| comment | User comment |
| config_type / usage_type | Config classification |
| family_count / nvt_count | Number of families/NVTs in the config |
| creation_time / modification_time | GVM audit timestamps |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASConfig)
(:OpenVASTask)-[:USES]->(:OpenVASConfig)
```

### OpenVASSchedule

A schedule that triggers tasks periodically.

| Field | Description |
|---|---|
| **id** | Schedule UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | Schedule name |
| comment | User comment |
| timezone | IANA timezone of the schedule |
| icalendar | iCalendar recurrence definition |
| next_run | Timestamp of the next scheduled run |
| creation_time / modification_time | GVM audit timestamps |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASSchedule)
(:OpenVASTask)-[:USES]->(:OpenVASSchedule)
```

### OpenVASPortList

A named list of ports/tags used by targets.

| Field | Description |
|---|---|
| **id** | Port list UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | Port list name |
| comment | User comment |
| port_count | Number of ports in the list |
| creation_time / modification_time | GVM audit timestamps |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASPortList)
(:OpenVASTarget)-[:USES]->(:OpenVASPortList)
```

### OpenVASCredential

A credential used for authenticated scans. Secret material is never ingested.

| Field | Description |
|---|---|
| **id** | Credential UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | Credential name |
| comment | User comment |
| credential_type | Type (e.g. `up`, `smb`, `esxi`, `snmp`) |
| allow_insecure | Whether insecure usage is allowed |
| creation_time / modification_time | GVM audit timestamps |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASCredential)
(:OpenVASTarget)-[:USES_SSH_CREDENTIAL]->(:OpenVASCredential)
(:OpenVASTarget)-[:USES_SMB_CREDENTIAL]->(:OpenVASCredential)
(:OpenVASTarget)-[:USES_ESXI_CREDENTIAL]->(:OpenVASCredential)
(:OpenVASTarget)-[:USES_SNMP_CREDENTIAL]->(:OpenVASCredential)
```

### OpenVASResult

A vulnerability instance detected by a scan on a specific host. Only results created within the configured lookback window are synced.

> **Ontology note:** when `has_cve` is `"true"` the node is also labelled `CVE`, allowing `CVEMetadata` nodes to enrich it automatically via `(:CVEMetadata)-[:ENRICHES]->(:CVE)` (matched on `cve_id`).

| Field | Description |
|---|---|
| **id** | Result UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | NVT name (e.g. `Microsoft Windows ...`) |
| **host** | IP address the finding was detected on (indexed) |
| hostname | Hostname of the affected host |
| port | Port/protocol the finding was detected on (e.g. `139/tcp`) |
| nvt_id | OID of the detecting NVT |
| **task_id** | UUID of the scan task that produced the finding (indexed) |
| task_name | Name of that task |
| severity | Numeric severity (0.0–10.0) |
| threat | Qualitative threat level (e.g. `High`, `Log`) |
| original_threat | Threat level before overrides |
| qod / qod_type | Quality of detection |
| description / summary / detection_result | Finding details |
| source_ip | IP of the scanner |
| created | Timestamp when the finding was created |
| **cve_id** | First CVE ID referenced by the NVT; used for CVEMetadata ontology matching (indexed) |
| cve_list | Full list of CVE IDs referenced by the NVT |
| has_cve | `"true"` if the NVT references at least one CVE ID, `"false"` otherwise |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASResult)
(:OpenVASResult)-[:AFFECTS]->(:OpenVASHost)
(:OpenVASResult)-[:DETECTED_BY]->(:OpenVASNVT)
(:OpenVASResult)-[:PART_OF_SCAN]->(:OpenVASTask)
```

### OpenVASNVT

A Network Vulnerability Test that detected one or more results. NVTs are deduplicated by OID across results — a single `OpenVASNVT` node can be linked to many `OpenVASResult` nodes.

| Field | Description |
|---|---|
| **id** | NVT OID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | NVT name |
| **oid** | NVT OID (indexed) |
| family | NVT family (e.g. `General`) |
| severity | Numeric severity (0.0–10.0) |
| cvss_base / cvss_base_vector | CVSS v2 base score and vector |
| solution | Remediation guidance |
| qod / qod_type | Quality of detection |
| description | NVT description |
| cve_list | Full list of CVE IDs referenced by the NVT |
| tags | NVT tags (CVSS metrics, CVE mappings, etc.) |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASNVT)
(:OpenVASResult)-[:DETECTED_BY]->(:OpenVASNVT)
(:OpenVASNVT)-[:HAS_CVE]->(:CVE)
```

The `HAS_CVE` edge materializes when the referenced `(:CVE)` nodes exist in the graph (e.g. after a `cve_metadata` sync), matching on the NVT's `cve_list`.

### OpenVASTLSCertificate

A TLS certificate observed by GVM during scans. Carries the cross-provider `Certificate` label, so it matches `(:Certificate)` alongside other certificate sources.

| Field | Description |
|---|---|
| **id** | Certificate UUID |
| instance_id | ID of the owning `OpenVASInstance` |
| name | Certificate name (IP or hostname it was observed on) |
| subject / issuer | Certificate subject and issuer |
| not_before / not_after | Validity window |
| serial | Serial number |
| fingerprint | Certificate fingerprint |
| certificate_format | Format (e.g. `CKM_PKIX`) |
| key_type / key_bits | Public key type and size |
| activation_time / expiry_time | GVM activation/expiry timestamps |
| source_type | How the certificate was discovered |
| status | Certificate status |
| lastupdated | Timestamp of the last sync run |

#### Relationships

```
(:OpenVASInstance)-[:RESOURCE]->(:OpenVASTLSCertificate)
(:OpenVASTLSCertificate)-[:CERTIFICATE_FOR]->(:OpenVASHost)
```

`CERTIFICATE_FOR` links a certificate to the host matching its name (IP or hostname). Hosts without a matching certificate, and certificates without a matching host, are not connected.