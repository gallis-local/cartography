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
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import DEVICE_INSTANCE


@dataclass(frozen=True)
class OpenVASHostNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The host's IP address, which is its stable identity across syncs.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef(
        "OPENVAS_INSTANCE_ID",
        set_in_kwargs=True,
        description="Id of the OpenVASInstance (GVM deployment) this resource belongs to.",
    )
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
        "latest_scan_date",
        description="Set by analysis job. Creation time of this host's most recent finding.",
    )  # Populated by OPENVAS_HOST_LATEST_SCAN.
    latest_scan_task_id: PropertyRef = PropertyRef(
        "latest_scan_task_id",
        description="Set by analysis job. GVM UUID of the task that most recently scanned this host.",
    )  # Populated by OPENVAS_HOST_LATEST_SCAN.
    latest_scan_task_name: PropertyRef = PropertyRef(
        "latest_scan_task_name",
        description="Set by analysis job. Display name of the task that most recently scanned this host.",
    )  # Populated by OPENVAS_HOST_LATEST_SCAN.
    source_type: PropertyRef = PropertyRef(
        "source_type",
        description="How GVM identified this host (e.g. by IP, hostname).",
    )
    identifiers: PropertyRef = PropertyRef(
        "identifiers",
        description="Comma-separated kinds of identifier GVM holds for this host (e.g. ip,hostname,OS).",
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
class OpenVASHostSchema(CartographyNodeSchema):
    """A host asset tracked by GVM's asset management, with its latest scan results."""

    label: str = "OpenVASHost"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DEVICE_INSTANCE])
    properties: OpenVASHostNodeProperties = OpenVASHostNodeProperties()
    sub_resource_relationship: OpenVASHostToInstanceRel = OpenVASHostToInstanceRel()
