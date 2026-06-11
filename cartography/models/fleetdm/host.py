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


@dataclass(frozen=True)
class FleetDMHostNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    display_name: PropertyRef = PropertyRef("display_name")
    uuid: PropertyRef = PropertyRef("uuid", extra_index=True)
    platform: PropertyRef = PropertyRef("platform")
    os_version: PropertyRef = PropertyRef("os_version")
    osquery_version: PropertyRef = PropertyRef("osquery_version")
    build: PropertyRef = PropertyRef("build")
    platform_like: PropertyRef = PropertyRef("platform_like")
    code_name: PropertyRef = PropertyRef("code_name")
    cpu_type: PropertyRef = PropertyRef("cpu_type")
    cpu_subtype: PropertyRef = PropertyRef("cpu_subtype")
    cpu_brand: PropertyRef = PropertyRef("cpu_brand")
    cpu_physical_cores: PropertyRef = PropertyRef("cpu_physical_cores")
    cpu_logical_cores: PropertyRef = PropertyRef("cpu_logical_cores")
    hardware_vendor: PropertyRef = PropertyRef("hardware_vendor")
    hardware_model: PropertyRef = PropertyRef("hardware_model")
    hardware_version: PropertyRef = PropertyRef("hardware_version")
    hardware_serial: PropertyRef = PropertyRef("hardware_serial", extra_index=True)
    computer_name: PropertyRef = PropertyRef("computer_name")
    memory: PropertyRef = PropertyRef("memory")
    uptime: PropertyRef = PropertyRef("uptime")
    public_ip: PropertyRef = PropertyRef("public_ip")
    primary_ip: PropertyRef = PropertyRef("primary_ip")
    primary_mac: PropertyRef = PropertyRef("primary_mac")
    status: PropertyRef = PropertyRef("status")
    seen_time: PropertyRef = PropertyRef("seen_time")
    last_enrolled_at: PropertyRef = PropertyRef("last_enrolled_at")
    distributed_interval: PropertyRef = PropertyRef("distributed_interval")
    config_tls_refresh: PropertyRef = PropertyRef("config_tls_refresh")
    logger_tls_period: PropertyRef = PropertyRef("logger_tls_period")
    gigs_disk_space_available: PropertyRef = PropertyRef("gigs_disk_space_available")
    percent_disk_space_available: PropertyRef = PropertyRef(
        "percent_disk_space_available",
    )
    gigs_total_disk_space: PropertyRef = PropertyRef("gigs_total_disk_space")
    team_name: PropertyRef = PropertyRef("team_name")
    fleet_name: PropertyRef = PropertyRef("fleet_name")
    failing_policies_count: PropertyRef = PropertyRef("failing_policies_count")
    critical_vulnerabilities_count: PropertyRef = PropertyRef(
        "critical_vulnerabilities_count",
    )
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    last_restarted_at: PropertyRef = PropertyRef("last_restarted_at")


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
class FleetDMHostSchema(CartographyNodeSchema):
    label: str = "FleetDMHost"
    properties: FleetDMHostNodeProperties = FleetDMHostNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Device"])
    sub_resource_relationship: FleetDMHostToTenantRel = FleetDMHostToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            FleetDMHostToFleetRel(),
        ]
    )
