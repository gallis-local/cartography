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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    comment: PropertyRef = PropertyRef("comment")
    status: PropertyRef = PropertyRef("status")
    alterable: PropertyRef = PropertyRef("alterable")
    creation_time: PropertyRef = PropertyRef("creation_time")
    modification_time: PropertyRef = PropertyRef("modification_time")
    last_report_id: PropertyRef = PropertyRef("last_report_id")
    last_report_timestamp: PropertyRef = PropertyRef("last_report_timestamp")
    last_report_severity: PropertyRef = PropertyRef("last_report_severity")
    last_report_scan_start: PropertyRef = PropertyRef("last_report_scan_start")
    last_report_scan_end: PropertyRef = PropertyRef("last_report_scan_end")
    target_id: PropertyRef = PropertyRef("target_id")
    target_name: PropertyRef = PropertyRef("target_name")
    config_id: PropertyRef = PropertyRef("config_id")
    config_name: PropertyRef = PropertyRef("config_name")
    schedule_id: PropertyRef = PropertyRef("schedule_id")
    schedule_name: PropertyRef = PropertyRef("schedule_name")


@dataclass(frozen=True)
class OpenVASTaskToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASTask)
@dataclass(frozen=True)
class OpenVASTaskToInstanceRel(CartographyRelSchema):
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


# (:OpenVASTask)-[:SCANS]->(:OpenVASTarget)
@dataclass(frozen=True)
class OpenVASTaskToTargetRel(CartographyRelSchema):
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


# (:OpenVASTask)-[:USES]->(:OpenVASConfig)
@dataclass(frozen=True)
class OpenVASTaskToConfigRel(CartographyRelSchema):
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


# (:OpenVASTask)-[:USES]->(:OpenVASSchedule)
@dataclass(frozen=True)
class OpenVASTaskToScheduleRel(CartographyRelSchema):
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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    comment: PropertyRef = PropertyRef("comment")
    creation_time: PropertyRef = PropertyRef("creation_time")
    modification_time: PropertyRef = PropertyRef("modification_time")
    hosts: PropertyRef = PropertyRef("hosts")
    max_hosts: PropertyRef = PropertyRef("max_hosts")
    exclude_hosts: PropertyRef = PropertyRef("exclude_hosts")
    port_list_id: PropertyRef = PropertyRef("port_list_id")
    port_list_name: PropertyRef = PropertyRef("port_list_name")
    alive_test: PropertyRef = PropertyRef("alive_test")
    allow_simultaneous_ips: PropertyRef = PropertyRef("allow_simultaneous_ips")
    reverse_lookup_only: PropertyRef = PropertyRef("reverse_lookup_only")
    reverse_lookup_unify: PropertyRef = PropertyRef("reverse_lookup_unify")
    ssh_credential_id: PropertyRef = PropertyRef("ssh_credential_id")
    smb_credential_id: PropertyRef = PropertyRef("smb_credential_id")
    esxi_credential_id: PropertyRef = PropertyRef("esxi_credential_id")
    snmp_credential_id: PropertyRef = PropertyRef("snmp_credential_id")


@dataclass(frozen=True)
class OpenVASTargetToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASTarget)
@dataclass(frozen=True)
class OpenVASTargetToInstanceRel(CartographyRelSchema):
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


# (:OpenVASTarget)-[:USES]->(:OpenVASPortList)
@dataclass(frozen=True)
class OpenVASTargetToPortListRel(CartographyRelSchema):
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


# (:OpenVASTarget)-[:USES_SSH_CREDENTIAL]->(:OpenVASCredential)
@dataclass(frozen=True)
class OpenVASTargetToSSHCredentialRel(CartographyRelSchema):
    target_node_label: str = "OpenVASCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ssh_credential_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SSH_CREDENTIAL"
    properties: OpenVASTargetToCredentialRelProperties = (
        OpenVASTargetToCredentialRelProperties()
    )


# (:OpenVASTarget)-[:USES_SMB_CREDENTIAL]->(:OpenVASCredential)
@dataclass(frozen=True)
class OpenVASTargetToSMBCredentialRel(CartographyRelSchema):
    target_node_label: str = "OpenVASCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("smb_credential_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SMB_CREDENTIAL"
    properties: OpenVASTargetToCredentialRelProperties = (
        OpenVASTargetToCredentialRelProperties()
    )


# (:OpenVASTarget)-[:USES_ESXI_CREDENTIAL]->(:OpenVASCredential)
@dataclass(frozen=True)
class OpenVASTargetToESXICredentialRel(CartographyRelSchema):
    target_node_label: str = "OpenVASCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("esxi_credential_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_ESXI_CREDENTIAL"
    properties: OpenVASTargetToCredentialRelProperties = (
        OpenVASTargetToCredentialRelProperties()
    )


# (:OpenVASTarget)-[:USES_SNMP_CREDENTIAL]->(:OpenVASCredential)
@dataclass(frozen=True)
class OpenVASTargetToSNMPCredentialRel(CartographyRelSchema):
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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    comment: PropertyRef = PropertyRef("comment")
    config_type: PropertyRef = PropertyRef("config_type")
    usage_type: PropertyRef = PropertyRef("usage_type")
    family_count: PropertyRef = PropertyRef("family_count")
    nvt_count: PropertyRef = PropertyRef("nvt_count")
    creation_time: PropertyRef = PropertyRef("creation_time")
    modification_time: PropertyRef = PropertyRef("modification_time")


@dataclass(frozen=True)
class OpenVASConfigToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASConfig)
@dataclass(frozen=True)
class OpenVASConfigToInstanceRel(CartographyRelSchema):
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
    label: str = "OpenVASConfig"
    properties: OpenVASConfigNodeProperties = OpenVASConfigNodeProperties()
    sub_resource_relationship: OpenVASConfigToInstanceRel = OpenVASConfigToInstanceRel()


@dataclass(frozen=True)
class OpenVASScheduleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    comment: PropertyRef = PropertyRef("comment")
    timezone: PropertyRef = PropertyRef("timezone")
    icalendar: PropertyRef = PropertyRef("icalendar")
    next_run: PropertyRef = PropertyRef("next_run")
    creation_time: PropertyRef = PropertyRef("creation_time")
    modification_time: PropertyRef = PropertyRef("modification_time")


@dataclass(frozen=True)
class OpenVASScheduleToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASSchedule)
@dataclass(frozen=True)
class OpenVASScheduleToInstanceRel(CartographyRelSchema):
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
    label: str = "OpenVASSchedule"
    properties: OpenVASScheduleNodeProperties = OpenVASScheduleNodeProperties()
    sub_resource_relationship: OpenVASScheduleToInstanceRel = (
        OpenVASScheduleToInstanceRel()
    )
