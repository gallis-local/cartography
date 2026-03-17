from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class UnifiFirewallZoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    attr_no_edit: PropertyRef = PropertyRef("attr_no_edit")
    default_zone: PropertyRef = PropertyRef("default_zone")
    zone_key: PropertyRef = PropertyRef("zone_key")
    network_ids: PropertyRef = PropertyRef("network_ids")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiFirewallZoneToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiFirewallZone)
class UnifiFirewallZoneToSiteRel(CartographyRelSchema):
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
    label: str = "UnifiFirewallZone"
    properties: UnifiFirewallZoneNodeProperties = UnifiFirewallZoneNodeProperties()
    sub_resource_relationship: UnifiFirewallZoneToSiteRel = UnifiFirewallZoneToSiteRel()
