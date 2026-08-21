"""
Data models for OpenVAS tasks (scans), targets, scan configs and schedules.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OpenVASTaskNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The GVM UUID of this scan task.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="The task's display name.")
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment set on the task."
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Current task status as reported by GVM (e.g. Done, Running, New, Stopped).",
    )
    alterable: PropertyRef = PropertyRef(
        "alterable",
        description="Whether the task's configuration can still be edited.",
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When the task was created."
    )
    modification_time: PropertyRef = PropertyRef(
        "modification_time", description="When the task was last modified."
    )
    last_report_id: PropertyRef = PropertyRef(
        "last_report_id", description="GVM UUID of the task's most recent scan report."
    )
    last_report_timestamp: PropertyRef = PropertyRef(
        "last_report_timestamp",
        description="Timestamp of the task's most recent scan report.",
    )
    last_report_severity: PropertyRef = PropertyRef(
        "last_report_severity",
        description="Highest CVSS severity recorded in the task's most recent report.",
    )
    last_report_scan_start: PropertyRef = PropertyRef(
        "last_report_scan_start", description="Start time of the most recent scan run."
    )
    last_report_scan_end: PropertyRef = PropertyRef(
        "last_report_scan_end", description="End time of the most recent scan run."
    )
    target_id: PropertyRef = PropertyRef(
        "target_id", description="GVM UUID of the OpenVASTarget this task scans."
    )
    target_name: PropertyRef = PropertyRef(
        "target_name", description="Display name of the task's target."
    )
    config_id: PropertyRef = PropertyRef(
        "config_id",
        description="GVM UUID of the scan config (OpenVASConfig) used by this task.",
    )
    config_name: PropertyRef = PropertyRef(
        "config_name", description="Display name of the task's scan config."
    )
    schedule_id: PropertyRef = PropertyRef(
        "schedule_id",
        description="GVM UUID of the schedule (OpenVASSchedule) driving this task, if any.",
    )
    schedule_name: PropertyRef = PropertyRef(
        "schedule_name", description="Display name of the task's schedule, if any."
    )


@dataclass(frozen=True)
class OpenVASTaskToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASTask)
class OpenVASTaskToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this scan task."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASTaskToInstanceRelProperties = (
        OpenVASTaskToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASTaskToTargetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASTask)-[:SCANS]->(:OpenVASTarget)
class OpenVASTaskToTargetRel(CartographyRelSchema):
    """The OpenVASTarget that this scan task scans."""

    target_node_label: str = "OpenVASTarget"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANS"
    properties: OpenVASTaskToTargetRelProperties = OpenVASTaskToTargetRelProperties()


@dataclass(frozen=True)
class OpenVASTaskToConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASTask)-[:USES]->(:OpenVASConfig)
class OpenVASTaskToConfigRel(CartographyRelSchema):
    """The scan config (OpenVASConfig) this task runs with."""

    target_node_label: str = "OpenVASConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("config_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: OpenVASTaskToConfigRelProperties = OpenVASTaskToConfigRelProperties()


@dataclass(frozen=True)
class OpenVASTaskToScheduleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASTask)-[:USES]->(:OpenVASSchedule)
class OpenVASTaskToScheduleRel(CartographyRelSchema):
    """The schedule (OpenVASSchedule) that triggers this task, if any."""

    target_node_label: str = "OpenVASSchedule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("schedule_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: OpenVASTaskToScheduleRelProperties = (
        OpenVASTaskToScheduleRelProperties()
    )


@dataclass(frozen=True)
class OpenVASTaskSchema(CartographyNodeSchema):
    """A GVM scan task: the definition of a recurring or one-off vulnerability scan."""

    label: str = "OpenVASTask"
    properties: OpenVASTaskNodeProperties = OpenVASTaskNodeProperties()
    sub_resource_relationship: OpenVASTaskToInstanceRel = OpenVASTaskToInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpenVASTaskToTargetRel(),
            OpenVASTaskToConfigRel(),
            OpenVASTaskToScheduleRel(),
        ],
    )


@dataclass(frozen=True)
class OpenVASTargetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The GVM UUID of this scan target.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="The target's display name.")
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment set on the target."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When the target was created."
    )
    modification_time: PropertyRef = PropertyRef(
        "modification_time", description="When the target was last modified."
    )
    hosts: PropertyRef = PropertyRef(
        "hosts",
        description="Comma-separated list of hosts/CIDRs included in the target.",
    )
    max_hosts: PropertyRef = PropertyRef(
        "max_hosts", description="Number of hosts the target expands to."
    )
    exclude_hosts: PropertyRef = PropertyRef(
        "exclude_hosts",
        description="Comma-separated list of hosts/CIDRs excluded from the target.",
    )
    port_list_id: PropertyRef = PropertyRef(
        "port_list_id",
        description="GVM UUID of the port list (OpenVASPortList) used to scope scanning.",
    )
    port_list_name: PropertyRef = PropertyRef(
        "port_list_name", description="Display name of the target's port list."
    )
    alive_test: PropertyRef = PropertyRef(
        "alive_test",
        description="Method GVM uses to determine if a host is alive before scanning it.",
    )
    allow_simultaneous_ips: PropertyRef = PropertyRef(
        "allow_simultaneous_ips",
        description="Whether GVM may scan multiple IPs of the same host in parallel.",
    )
    reverse_lookup_only: PropertyRef = PropertyRef(
        "reverse_lookup_only",
        description="Whether only hosts with a reverse-DNS record are scanned.",
    )
    reverse_lookup_unify: PropertyRef = PropertyRef(
        "reverse_lookup_unify",
        description="Whether hosts sharing a reverse-DNS name are treated as one host.",
    )
    ssh_credential_id: PropertyRef = PropertyRef(
        "ssh_credential_id",
        description="GVM UUID of the SSH credential used for authenticated scanning.",
    )
    smb_credential_id: PropertyRef = PropertyRef(
        "smb_credential_id",
        description="GVM UUID of the SMB credential used for authenticated scanning.",
    )
    esxi_credential_id: PropertyRef = PropertyRef(
        "esxi_credential_id",
        description="GVM UUID of the ESXi credential used for authenticated scanning.",
    )
    snmp_credential_id: PropertyRef = PropertyRef(
        "snmp_credential_id",
        description="GVM UUID of the SNMP credential used for authenticated scanning.",
    )


@dataclass(frozen=True)
class OpenVASTargetToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASTarget)
class OpenVASTargetToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this scan target."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASTargetToInstanceRelProperties = (
        OpenVASTargetToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASTargetToPortListRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASTarget)-[:USES]->(:OpenVASPortList)
class OpenVASTargetToPortListRel(CartographyRelSchema):
    """The port list (OpenVASPortList) that scopes this target's scanned ports."""

    target_node_label: str = "OpenVASPortList"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("port_list_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: OpenVASTargetToPortListRelProperties = (
        OpenVASTargetToPortListRelProperties()
    )


@dataclass(frozen=True)
class OpenVASTargetToCredentialRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASTarget)-[:USES_SSH_CREDENTIAL]->(:OpenVASCredential)
class OpenVASTargetToSSHCredentialRel(CartographyRelSchema):
    """The SSH credential (OpenVASCredential) this target authenticates with."""

    target_node_label: str = "OpenVASCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ssh_credential_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SSH_CREDENTIAL"
    properties: OpenVASTargetToCredentialRelProperties = (
        OpenVASTargetToCredentialRelProperties()
    )


@dataclass(frozen=True)
# (:OpenVASTarget)-[:USES_SMB_CREDENTIAL]->(:OpenVASCredential)
class OpenVASTargetToSMBCredentialRel(CartographyRelSchema):
    """The SMB credential (OpenVASCredential) this target authenticates with."""

    target_node_label: str = "OpenVASCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("smb_credential_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SMB_CREDENTIAL"
    properties: OpenVASTargetToCredentialRelProperties = (
        OpenVASTargetToCredentialRelProperties()
    )


@dataclass(frozen=True)
# (:OpenVASTarget)-[:USES_ESXI_CREDENTIAL]->(:OpenVASCredential)
class OpenVASTargetToESXICredentialRel(CartographyRelSchema):
    """The ESXi credential (OpenVASCredential) this target authenticates with."""

    target_node_label: str = "OpenVASCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("esxi_credential_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_ESXI_CREDENTIAL"
    properties: OpenVASTargetToCredentialRelProperties = (
        OpenVASTargetToCredentialRelProperties()
    )


@dataclass(frozen=True)
# (:OpenVASTarget)-[:USES_SNMP_CREDENTIAL]->(:OpenVASCredential)
class OpenVASTargetToSNMPCredentialRel(CartographyRelSchema):
    """The SNMP credential (OpenVASCredential) this target authenticates with."""

    target_node_label: str = "OpenVASCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("snmp_credential_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SNMP_CREDENTIAL"
    properties: OpenVASTargetToCredentialRelProperties = (
        OpenVASTargetToCredentialRelProperties()
    )


@dataclass(frozen=True)
class OpenVASTargetSchema(CartographyNodeSchema):
    """A GVM scan target: the set of hosts/ports/credentials a task scans."""

    label: str = "OpenVASTarget"
    properties: OpenVASTargetNodeProperties = OpenVASTargetNodeProperties()
    sub_resource_relationship: OpenVASTargetToInstanceRel = OpenVASTargetToInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpenVASTargetToPortListRel(),
            OpenVASTargetToSSHCredentialRel(),
            OpenVASTargetToSMBCredentialRel(),
            OpenVASTargetToESXICredentialRel(),
            OpenVASTargetToSNMPCredentialRel(),
        ],
    )


@dataclass(frozen=True)
class OpenVASConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The GVM UUID of this scan config.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="The scan config's display name."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment set on the scan config."
    )
    config_type: PropertyRef = PropertyRef(
        "config_type", description="GVM scan config type identifier."
    )
    usage_type: PropertyRef = PropertyRef(
        "usage_type", description="What this config is used for (e.g. scan, policy)."
    )
    family_count: PropertyRef = PropertyRef(
        "family_count", description="Number of NVT families enabled in this config."
    )
    nvt_count: PropertyRef = PropertyRef(
        "nvt_count", description="Number of individual NVTs enabled in this config."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When the scan config was created."
    )
    modification_time: PropertyRef = PropertyRef(
        "modification_time", description="When the scan config was last modified."
    )


@dataclass(frozen=True)
class OpenVASConfigToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASConfig)
class OpenVASConfigToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this scan config."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASConfigToInstanceRelProperties = (
        OpenVASConfigToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASConfigSchema(CartographyNodeSchema):
    """A GVM scan config: the set of NVT families/preferences a task scans with."""

    label: str = "OpenVASConfig"
    properties: OpenVASConfigNodeProperties = OpenVASConfigNodeProperties()
    sub_resource_relationship: OpenVASConfigToInstanceRel = OpenVASConfigToInstanceRel()


@dataclass(frozen=True)
class OpenVASScheduleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The GVM UUID of this schedule.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="The schedule's display name.")
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment set on the schedule."
    )
    timezone: PropertyRef = PropertyRef(
        "timezone", description="Timezone the schedule's recurrence is evaluated in."
    )
    icalendar: PropertyRef = PropertyRef(
        "icalendar", description="Raw iCalendar (RFC 5545) recurrence rule."
    )
    next_run: PropertyRef = PropertyRef(
        "next_run", description="When the schedule will next trigger its task."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When the schedule was created."
    )
    modification_time: PropertyRef = PropertyRef(
        "modification_time", description="When the schedule was last modified."
    )


@dataclass(frozen=True)
class OpenVASScheduleToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASSchedule)
class OpenVASScheduleToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this schedule."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASScheduleToInstanceRelProperties = (
        OpenVASScheduleToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASScheduleSchema(CartographyNodeSchema):
    """A GVM schedule: a recurrence rule that triggers a scan task automatically."""

    label: str = "OpenVASSchedule"
    properties: OpenVASScheduleNodeProperties = OpenVASScheduleNodeProperties()
    sub_resource_relationship: OpenVASScheduleToInstanceRel = (
        OpenVASScheduleToInstanceRel()
    )
