"""
Data model for OpenVAS hosts.
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
from cartography.models.ontology.labels import DEVICE_INSTANCE


@dataclass(frozen=True)
class OpenVASHostNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    ip: PropertyRef = PropertyRef("ip", extra_index=True)
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    os: PropertyRef = PropertyRef("os")
    comment: PropertyRef = PropertyRef("comment")
    creation_time: PropertyRef = PropertyRef("creation_time")
    modification_time: PropertyRef = PropertyRef("modification_time")
    severity: PropertyRef = PropertyRef("severity")
    asset_id: PropertyRef = PropertyRef("asset_id", extra_index=True)
    latest_scan_date: PropertyRef = PropertyRef("latest_scan_date")
    latest_scan_task_id: PropertyRef = PropertyRef("latest_scan_task_id")
    latest_scan_task_name: PropertyRef = PropertyRef("latest_scan_task_name")
    source_type: PropertyRef = PropertyRef("source_type")
    identifiers: PropertyRef = PropertyRef("identifiers")


@dataclass(frozen=True)
class OpenVASHostToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASHost)
@dataclass(frozen=True)
class OpenVASHostToInstanceRel(CartographyRelSchema):
    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASHostToInstanceRelProperties = (
        OpenVASHostToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASHostToTaskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASHost)-[:LAST_SCANNED_BY]->(:OpenVASTask)
@dataclass(frozen=True)
class OpenVASHostToTaskRel(CartographyRelSchema):
    target_node_label: str = "OpenVASTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("latest_scan_task_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LAST_SCANNED_BY"
    properties: OpenVASHostToTaskRelProperties = OpenVASHostToTaskRelProperties()


@dataclass(frozen=True)
class OpenVASHostSchema(CartographyNodeSchema):
    label: str = "OpenVASHost"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DEVICE_INSTANCE])
    properties: OpenVASHostNodeProperties = OpenVASHostNodeProperties()
    sub_resource_relationship: OpenVASHostToInstanceRel = OpenVASHostToInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpenVASHostToTaskRel(),
        ],
    )
