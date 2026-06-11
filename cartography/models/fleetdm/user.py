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
class FleetDMUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    global_role: PropertyRef = PropertyRef("global_role")
    sso_enabled: PropertyRef = PropertyRef("sso_enabled")
    mfa_enabled: PropertyRef = PropertyRef("mfa_enabled")
    api_only: PropertyRef = PropertyRef("api_only")
    force_password_reset: PropertyRef = PropertyRef("force_password_reset")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class FleetDMUserToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMUserToTenantRel(CartographyRelSchema):
    target_node_label: str = "FleetDMTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FleetDMUserToTenantRelProperties = FleetDMUserToTenantRelProperties()


@dataclass(frozen=True)
class FleetDMUserToHumanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FleetDMUserToHumanRel(CartographyRelSchema):
    target_node_label: str = "Human"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTITY_FLEETDM"
    properties: FleetDMUserToHumanRelProperties = FleetDMUserToHumanRelProperties()


@dataclass(frozen=True)
class FleetDMUserSchema(CartographyNodeSchema):
    label: str = "FleetDMUser"
    properties: FleetDMUserNodeProperties = FleetDMUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    sub_resource_relationship: FleetDMUserToTenantRel = FleetDMUserToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            FleetDMUserToHumanRel(),
        ]
    )
