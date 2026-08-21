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
    id: PropertyRef = PropertyRef("id", description="The GVM asset UUID of this host.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="The host's display name in GVM."
    )
    ip: PropertyRef = PropertyRef(
        "ip", extra_index=True, description="The host's IP address."
    )
    hostname: PropertyRef = PropertyRef(
        "hostname",
        extra_index=True,
        description="The host's resolved hostname, if known.",
    )
    os: PropertyRef = PropertyRef(
        "os", description="Operating system GVM fingerprinted for this host."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment set on the host asset."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When GVM first recorded this host asset."
    )
    modification_time: PropertyRef = PropertyRef(
        "modification_time", description="When this host asset was last modified."
    )
    severity: PropertyRef = PropertyRef(
        "severity", description="Highest CVSS severity among this host's findings."
    )
    asset_id: PropertyRef = PropertyRef(
        "asset_id",
        extra_index=True,
        description="GVM asset-management UUID for this host.",
    )
    latest_scan_date: PropertyRef = PropertyRef(
        "latest_scan_date", description="When this host was last scanned."
    )
    latest_scan_task_id: PropertyRef = PropertyRef(
        "latest_scan_task_id",
        description="GVM UUID of the task that most recently scanned this host.",
    )
    latest_scan_task_name: PropertyRef = PropertyRef(
        "latest_scan_task_name",
        description="Display name of the task that most recently scanned this host.",
    )
    source_type: PropertyRef = PropertyRef(
        "source_type",
        description="How GVM identified this host (e.g. by IP, hostname).",
    )
    identifiers: PropertyRef = PropertyRef(
        "identifiers",
        description="Additional GVM-reported identifiers for this host (e.g. MAC addresses).",
    )


@dataclass(frozen=True)
class OpenVASHostToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASHost)
@dataclass(frozen=True)
class OpenVASHostToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this host asset."""

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
    """The scan task that most recently scanned this host."""

    target_node_label: str = "OpenVASTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("latest_scan_task_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LAST_SCANNED_BY"
    properties: OpenVASHostToTaskRelProperties = OpenVASHostToTaskRelProperties()


@dataclass(frozen=True)
class OpenVASHostSchema(CartographyNodeSchema):
    """A host asset tracked by GVM's asset management, with its latest scan results."""

    label: str = "OpenVASHost"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DEVICE_INSTANCE])
    properties: OpenVASHostNodeProperties = OpenVASHostNodeProperties()
    sub_resource_relationship: OpenVASHostToInstanceRel = OpenVASHostToInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OpenVASHostToTaskRel(),
        ],
    )
