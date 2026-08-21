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
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import DEVICE


@dataclass(frozen=True)
class FleetDMHostNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this resource in Fleet."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef(
        "hostname",
        extra_index=True,
        description="Hostname reported by the host.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Human-readable display name."
    )
    uuid: PropertyRef = PropertyRef(
        "uuid",
        extra_index=True,
        description="Unique identifier (UUID) for the host, as reported by osquery.",
    )
    platform: PropertyRef = PropertyRef(
        "platform", description="Target platform(s) this resource applies to."
    )
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Operating system name and version running on the host.",
    )
    osquery_version: PropertyRef = PropertyRef(
        "osquery_version", description="Version of osquery running on the host."
    )
    build: PropertyRef = PropertyRef("build", description="OS build identifier.")
    platform_like: PropertyRef = PropertyRef(
        "platform_like", description="Platform family the host's OS is derived from."
    )
    code_name: PropertyRef = PropertyRef(
        "code_name", description="OS release code name."
    )
    cpu_type: PropertyRef = PropertyRef(
        "cpu_type", description="CPU type/architecture of the host."
    )
    cpu_subtype: PropertyRef = PropertyRef(
        "cpu_subtype", description="CPU subtype of the host."
    )
    cpu_brand: PropertyRef = PropertyRef("cpu_brand", description="CPU brand string.")
    cpu_physical_cores: PropertyRef = PropertyRef(
        "cpu_physical_cores", description="Number of physical CPU cores."
    )
    cpu_logical_cores: PropertyRef = PropertyRef(
        "cpu_logical_cores", description="Number of logical CPU cores."
    )
    hardware_vendor: PropertyRef = PropertyRef(
        "hardware_vendor", description="Hardware vendor of the host."
    )
    hardware_model: PropertyRef = PropertyRef(
        "hardware_model", description="Hardware model of the host."
    )
    hardware_version: PropertyRef = PropertyRef(
        "hardware_version", description="Hardware version of the host."
    )
    hardware_serial: PropertyRef = PropertyRef(
        "hardware_serial",
        extra_index=True,
        description="Hardware serial number of the host.",
    )
    computer_name: PropertyRef = PropertyRef(
        "computer_name", description="User-configured computer name of the host."
    )
    memory: PropertyRef = PropertyRef(
        "memory", description="Total physical memory of the host, in bytes."
    )
    uptime: PropertyRef = PropertyRef("uptime", description="Host uptime, in seconds.")
    public_ip: PropertyRef = PropertyRef(
        "public_ip", description="Public IP address the host last connected from."
    )
    primary_ip: PropertyRef = PropertyRef(
        "primary_ip", description="Primary internal IP address of the host."
    )
    primary_mac: PropertyRef = PropertyRef(
        "primary_mac", description="Primary MAC address of the host."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Fleet-reported online status of the host."
    )
    seen_time: PropertyRef = PropertyRef(
        "seen_time",
        description="Timestamp the host was last seen checking in to Fleet.",
    )
    last_enrolled_at: PropertyRef = PropertyRef(
        "last_enrolled_at", description="Timestamp the host last enrolled in Fleet."
    )
    distributed_interval: PropertyRef = PropertyRef(
        "distributed_interval",
        description="Osquery distributed query interval, in seconds.",
    )
    config_tls_refresh: PropertyRef = PropertyRef(
        "config_tls_refresh",
        description="Osquery configuration refresh interval, in seconds.",
    )
    logger_tls_period: PropertyRef = PropertyRef(
        "logger_tls_period", description="Osquery logger TLS period, in seconds."
    )
    gigs_disk_space_available: PropertyRef = PropertyRef(
        "gigs_disk_space_available",
        description="Available disk space on the host, in gigabytes.",
    )
    percent_disk_space_available: PropertyRef = PropertyRef(
        "percent_disk_space_available",
        description="Percentage of disk space available on the host.",
    )
    gigs_total_disk_space: PropertyRef = PropertyRef(
        "gigs_total_disk_space",
        description="Total disk space on the host, in gigabytes.",
    )
    team_name: PropertyRef = PropertyRef(
        "team_name", description="Name of the Fleet team the host belongs to."
    )
    fleet_name: PropertyRef = PropertyRef(
        "fleet_name", description="Name of the Fleet the host belongs to."
    )
    failing_policies_count: PropertyRef = PropertyRef(
        "failing_policies_count",
        description="Number of policies the host is currently failing.",
    )
    critical_vulnerabilities_count: PropertyRef = PropertyRef(
        "critical_vulnerabilities_count",
        description="Number of critical vulnerabilities affecting the host.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the resource was created in Fleet."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the resource was last updated in Fleet.",
    )
    last_restarted_at: PropertyRef = PropertyRef(
        "last_restarted_at", description="Timestamp the host was last restarted."
    )
    team_id: PropertyRef = PropertyRef(
        "team_id", description="ID of the Fleet team the host belongs to."
    )
    mdm_enrollment_status: PropertyRef = PropertyRef(
        "mdm_enrollment_status",
        description="Mobile device management (MDM) enrollment status of the host.",
    )
    mdm_name: PropertyRef = PropertyRef(
        "mdm_name", description="Name of the MDM solution managing the host, if any."
    )
    mdm_server_url: PropertyRef = PropertyRef(
        "mdm_server_url", description="URL of the MDM server managing the host, if any."
    )
    geolocation_country_iso: PropertyRef = PropertyRef(
        "geolocation_country_iso",
        description="ISO country code of the host's last known location, derived from its public IP.",
    )
    geolocation_city_name: PropertyRef = PropertyRef(
        "geolocation_city_name",
        description="City name of the host's last known location, derived from its public IP.",
    )


@dataclass(frozen=True)
class FleetDMHostToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMHostToTenantRel(CartographyRelSchema):
    target_node_label: str = "FleetDMTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FleetDMHostToTenantRelProperties = FleetDMHostToTenantRelProperties()


@dataclass(frozen=True)
class FleetDMHostToFleetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMHostToFleetRel(CartographyRelSchema):
    target_node_label: str = "FleetDMFleet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("fleet_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PART_OF_FLEET"
    properties: FleetDMHostToFleetRelProperties = FleetDMHostToFleetRelProperties()


@dataclass(frozen=True)
class FleetDMHostToSoftwareVersionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMHostToSoftwareVersionRel(CartographyRelSchema):
    """
    The host has this software version installed, per the Fleet API's per-host
    software inventory (`populate_software` on `GET /api/v1/fleet/hosts`).
    """

    target_node_label: str = "FleetDMSoftwareVersion"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("software_version_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SOFTWARE"
    properties: FleetDMHostToSoftwareVersionRelProperties = (
        FleetDMHostToSoftwareVersionRelProperties()
    )


@dataclass(frozen=True)
class FleetDMHostToLabelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMHostToLabelRel(CartographyRelSchema):
    """
    The host is a member of this label, per the Fleet API's per-host label
    membership (`populate_labels` on `GET /api/v1/fleet/hosts`).
    """

    target_node_label: str = "FleetDMLabel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("label_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_LABEL"
    properties: FleetDMHostToLabelRelProperties = FleetDMHostToLabelRelProperties()


@dataclass(frozen=True)
class FleetDMHostSchema(CartographyNodeSchema):
    label: str = "FleetDMHost"
    properties: FleetDMHostNodeProperties = FleetDMHostNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DEVICE])
    sub_resource_relationship: FleetDMHostToTenantRel = FleetDMHostToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            FleetDMHostToFleetRel(),
            FleetDMHostToSoftwareVersionRel(),
            FleetDMHostToLabelRel(),
        ]
    )


@dataclass(frozen=True)
class FleetDMHostToPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    response: PropertyRef = PropertyRef(
        "response",
        description="The host's result for this policy: 'pass', 'fail', or 'unsupported'.",
    )


@dataclass(frozen=True)
# (:FleetDMHost)-[:CHECKS]->(:FleetDMPolicy)
class FleetDMHostToPolicyMatchLink(CartographyRelSchema):
    """Records whether a host passes or fails a given policy check."""

    target_node_label: str = "FleetDMPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    source_node_label: str = "FleetDMHost"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("host_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CHECKS"
    properties: FleetDMHostToPolicyRelProperties = FleetDMHostToPolicyRelProperties()
