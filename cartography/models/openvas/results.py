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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    host: PropertyRef = PropertyRef("host", extra_index=True)
    hostname: PropertyRef = PropertyRef("hostname")
    port: PropertyRef = PropertyRef("port")
    nvt_id: PropertyRef = PropertyRef("nvt_id")
    task_id: PropertyRef = PropertyRef("task_id", extra_index=True)
    task_name: PropertyRef = PropertyRef("task_name")
    severity: PropertyRef = PropertyRef("severity")
    threat: PropertyRef = PropertyRef("threat")
    original_threat: PropertyRef = PropertyRef("original_threat")
    qod: PropertyRef = PropertyRef("qod")
    qod_type: PropertyRef = PropertyRef("qod_type")
    description: PropertyRef = PropertyRef("description")
    summary: PropertyRef = PropertyRef("summary")
    detection_result: PropertyRef = PropertyRef("detection_result")
    source_ip: PropertyRef = PropertyRef("source_ip")
    created: PropertyRef = PropertyRef("created")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    cve_list: PropertyRef = PropertyRef("cve_list")
    has_cve: PropertyRef = PropertyRef("has_cve")


@dataclass(frozen=True)
class OpenVASResultToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASResult)
@dataclass(frozen=True)
class OpenVASResultToInstanceRel(CartographyRelSchema):
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


# (:OpenVASResult)-[:AFFECTS]->(:OpenVASHost)
@dataclass(frozen=True)
class OpenVASResultToHostRel(CartographyRelSchema):
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


# (:OpenVASResult)-[:DETECTED_BY]->(:OpenVASNVT)
@dataclass(frozen=True)
class OpenVASResultToNVTRel(CartographyRelSchema):
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


# (:OpenVASResult)-[:PART_OF_SCAN]->(:OpenVASTask)
@dataclass(frozen=True)
class OpenVASResultToTaskRel(CartographyRelSchema):
    target_node_label: str = "OpenVASTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("task_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SCAN"
    properties: OpenVASResultToTaskRelProperties = OpenVASResultToTaskRelProperties()


@dataclass(frozen=True)
class OpenVASResultSchema(CartographyNodeSchema):
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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    oid: PropertyRef = PropertyRef("oid", extra_index=True)
    family: PropertyRef = PropertyRef("family")
    severity: PropertyRef = PropertyRef("severity")
    cvss_base: PropertyRef = PropertyRef("cvss_base")
    cvss_base_vector: PropertyRef = PropertyRef("cvss_base_vector")
    solution: PropertyRef = PropertyRef("solution")
    qod: PropertyRef = PropertyRef("qod")
    qod_type: PropertyRef = PropertyRef("qod_type")
    description: PropertyRef = PropertyRef("description")
    cve_list: PropertyRef = PropertyRef("cve_list")
    tags: PropertyRef = PropertyRef("tags")


@dataclass(frozen=True)
class OpenVASNVTToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASNVT)
@dataclass(frozen=True)
class OpenVASNVTToInstanceRel(CartographyRelSchema):
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


# (:OpenVASNVT)-[:HAS_CVE]->(:CVE)
@dataclass(frozen=True)
class OpenVASNVTToCVEPerInstanceRel(CartographyRelSchema):
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
    label: str = "OpenVASNVT"
    properties: OpenVASNVTNodeProperties = OpenVASNVTNodeProperties()
    sub_resource_relationship: OpenVASNVTToInstanceRel = OpenVASNVTToInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpenVASNVTToCVEPerInstanceRel(),
        ],
    )
