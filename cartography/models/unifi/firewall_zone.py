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
from cartography.models.unifi.extra_labels import NETWORK_ZONE


@dataclass(frozen=True)
class UnifiFirewallZoneNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiFirewallZone."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Name.")
    attr_no_edit: PropertyRef = PropertyRef("attr_no_edit", description="Attr no edit.")
    default_zone: PropertyRef = PropertyRef("default_zone", description="Default zone.")
    zone_key: PropertyRef = PropertyRef("zone_key", description="Zone key.")
    network_ids: PropertyRef = PropertyRef("network_ids", description="Network ids.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiFirewallZoneToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiFirewallZoneToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiFirewallZone)
class UnifiFirewallZoneToSiteRel(CartographyRelSchema):
    """Relationship: UnifiFirewallZoneToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiFirewallZoneToSiteRelProperties = (
        UnifiFirewallZoneToSiteRelProperties()
    )


@dataclass(frozen=True)
class UnifiFirewallZoneSchema(CartographyNodeSchema):
    """A UnifiFirewallZone."""

    label: str = "UnifiFirewallZone"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ZONE])
    properties: UnifiFirewallZoneNodeProperties = UnifiFirewallZoneNodeProperties()
    sub_resource_relationship: UnifiFirewallZoneToSiteRel = UnifiFirewallZoneToSiteRel()
