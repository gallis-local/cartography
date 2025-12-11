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
class UnifiTrafficRouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    description: PropertyRef = PropertyRef("description")
    enabled: PropertyRef = PropertyRef("enabled")
    matching_target: PropertyRef = PropertyRef("matching_target")
    network_id: PropertyRef = PropertyRef("network_id")
    next_hop: PropertyRef = PropertyRef("next_hop")


@dataclass(frozen=True)
class UnifiTrafficRouteToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)<-[:RESOURCE]-(:UnifiTrafficRoute)
class UnifiTrafficRouteToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiTrafficRouteToSiteRelProperties = (
        UnifiTrafficRouteToSiteRelProperties()
    )


@dataclass(frozen=True)
class UnifiTrafficRouteSchema(CartographyNodeSchema):
    label: str = "UnifiTrafficRoute"
    properties: UnifiTrafficRouteNodeProperties = UnifiTrafficRouteNodeProperties()
    sub_resource_relationship: UnifiTrafficRouteToSiteRel = UnifiTrafficRouteToSiteRel()
