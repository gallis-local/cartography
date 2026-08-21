"""
Data models for OpenVAS scan results (findings) and NVTs.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import CVE


@dataclass(frozen=True)
class OpenVASResultNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The GVM UUID of this scan result.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="The result's display name (usually the NVT name)."
    )
    host: PropertyRef = PropertyRef(
        "host",
        extra_index=True,
        description="IP address of the host this finding was detected on.",
    )
    hostname: PropertyRef = PropertyRef(
        "hostname", description="Hostname of the affected host, if known."
    )
    port: PropertyRef = PropertyRef(
        "port", description="Port/protocol the finding was detected on."
    )
    nvt_id: PropertyRef = PropertyRef(
        "nvt_id", description="OID of the NVT (OpenVASNVT) that produced this finding."
    )
    task_id: PropertyRef = PropertyRef(
        "task_id",
        extra_index=True,
        description="GVM UUID of the scan task that produced this finding.",
    )
    task_name: PropertyRef = PropertyRef(
        "task_name",
        description="Display name of the scan task that produced this finding.",
    )
    severity: PropertyRef = PropertyRef(
        "severity", description="CVSS severity score of the finding."
    )
    threat: PropertyRef = PropertyRef(
        "threat",
        description="GVM threat level (e.g. High, Medium, Low, Log) derived from severity.",
    )
    original_threat: PropertyRef = PropertyRef(
        "original_threat",
        description="Threat level as originally reported, before any override.",
    )
    qod: PropertyRef = PropertyRef(
        "qod",
        description="Quality of Detection percentage GVM assigns to this finding.",
    )
    qod_type: PropertyRef = PropertyRef(
        "qod_type",
        description="Detection method used to determine QOD (e.g. remote_banner, exploit).",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Human-readable description of the finding."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Short summary of the underlying NVT/vulnerability."
    )
    detection_result: PropertyRef = PropertyRef(
        "detection_result",
        description="Raw detection evidence reported by the NVT (e.g. banner text).",
    )
    source_ip: PropertyRef = PropertyRef(
        "source_ip", description="Source IP GVM scanned from, when reported."
    )
    created: PropertyRef = PropertyRef(
        "created", description="When this result was created."
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="Primary CVE identifier associated with this finding, if any.",
    )
    cve_list: PropertyRef = PropertyRef(
        "cve_list", description="All CVE identifiers associated with this finding."
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve",
        description="Whether this finding has at least one associated CVE (drives the CVE extra label).",
    )


@dataclass(frozen=True)
class OpenVASResultToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASResult)
class OpenVASResultToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this scan result."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASResultToInstanceRelProperties = (
        OpenVASResultToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASResultToHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASResult)-[:AFFECTS]->(:OpenVASHost)
class OpenVASResultToHostRel(CartographyRelSchema):
    """The host asset this finding affects."""

    target_node_label: str = "OpenVASHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ip": PropertyRef("host")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: OpenVASResultToHostRelProperties = OpenVASResultToHostRelProperties()


@dataclass(frozen=True)
class OpenVASResultToNVTRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASResult)-[:DETECTED_BY]->(:OpenVASNVT)
class OpenVASResultToNVTRel(CartographyRelSchema):
    """The NVT (vulnerability test) that produced this finding."""

    target_node_label: str = "OpenVASNVT"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("nvt_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_BY"
    properties: OpenVASResultToNVTRelProperties = OpenVASResultToNVTRelProperties()


@dataclass(frozen=True)
class OpenVASResultToTaskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASResult)-[:PART_OF_SCAN]->(:OpenVASTask)
class OpenVASResultToTaskRel(CartographyRelSchema):
    """The scan task run that produced this finding."""

    target_node_label: str = "OpenVASTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("task_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SCAN"
    properties: OpenVASResultToTaskRelProperties = OpenVASResultToTaskRelProperties()


@dataclass(frozen=True)
class OpenVASResultSchema(CartographyNodeSchema):
    """A single vulnerability finding from a GVM scan report."""

    label: str = "OpenVASResult"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            CVE.when(has_cve="true"),
        ],
    )
    properties: OpenVASResultNodeProperties = OpenVASResultNodeProperties()
    sub_resource_relationship: OpenVASResultToInstanceRel = OpenVASResultToInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpenVASResultToHostRel(),
            OpenVASResultToNVTRel(),
            OpenVASResultToTaskRel(),
        ],
    )


@dataclass(frozen=True)
class OpenVASNVTNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The OID (object identifier) of this Network Vulnerability Test.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="The NVT's display name.")
    oid: PropertyRef = PropertyRef(
        "oid",
        extra_index=True,
        description="The NVT's OID, duplicated here for indexed lookup.",
    )
    family: PropertyRef = PropertyRef(
        "family", description="NVT family/category this test belongs to."
    )
    severity: PropertyRef = PropertyRef(
        "severity", description="CVSS severity score associated with this NVT."
    )
    cvss_base: PropertyRef = PropertyRef(
        "cvss_base", description="Base CVSS score for this NVT."
    )
    cvss_base_vector: PropertyRef = PropertyRef(
        "cvss_base_vector", description="CVSS base vector string for this NVT."
    )
    solution: PropertyRef = PropertyRef(
        "solution", description="Recommended remediation text for this NVT."
    )
    solution_type: PropertyRef = PropertyRef(
        "solution_type",
        extra_index=True,
        description="Category of remediation (e.g. VendorFix, Mitigation, NoneAvailable, Workaround).",
    )
    solution_method: PropertyRef = PropertyRef(
        "solution_method",
        description="Delivery method of the solution (e.g. Patch, Update).",
    )
    qod: PropertyRef = PropertyRef(
        "qod", description="Default Quality of Detection percentage for this NVT."
    )
    qod_type: PropertyRef = PropertyRef(
        "qod_type", description="Default detection method type for this NVT."
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable description of the vulnerability this NVT checks for.",
    )
    cve_list: PropertyRef = PropertyRef(
        "cve_list", description="CVE identifiers associated with this NVT."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Raw GVM tag string with additional NVT metadata."
    )


@dataclass(frozen=True)
class OpenVASNVTToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASNVT)
class OpenVASNVTToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this NVT."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASNVTToInstanceRelProperties = OpenVASNVTToInstanceRelProperties()


@dataclass(frozen=True)
class OpenVASNVTToCVEPerInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASNVT)-[:HAS_CVE]->(:CVE)
class OpenVASNVTToCVEPerInstanceRel(CartographyRelSchema):
    """The CVE(s) this NVT tests for."""

    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_list", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_CVE"
    properties: OpenVASNVTToCVEPerInstanceRelProperties = (
        OpenVASNVTToCVEPerInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASNVTSchema(CartographyNodeSchema):
    """A GVM Network Vulnerability Test (NVT): a single check the scanner can run."""

    label: str = "OpenVASNVT"
    properties: OpenVASNVTNodeProperties = OpenVASNVTNodeProperties()
    sub_resource_relationship: OpenVASNVTToInstanceRel = OpenVASNVTToInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpenVASNVTToCVEPerInstanceRel(),
        ],
    )
