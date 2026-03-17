from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
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
    regions: PropertyRef = PropertyRef("regions")
    domains: PropertyRef = PropertyRef("domains")
    target_client_macs: PropertyRef = PropertyRef("target_client_macs")


@dataclass(frozen=True)
class UnifiTrafficRouteToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiTrafficRoute)
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
class UnifiTrafficRouteToClientRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiTrafficRoute)-[:APPLIES_TO_CLIENT]->(:UnifiClient)
class UnifiTrafficRouteToClientRel(CartographyRelSchema):
    target_node_label: str = "UnifiClient"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_client_macs", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO_CLIENT"
    properties: UnifiTrafficRouteToClientRelProperties = (
        UnifiTrafficRouteToClientRelProperties()
    )


@dataclass(frozen=True)
class UnifiTrafficRouteSchema(CartographyNodeSchema):
    label: str = "UnifiTrafficRoute"
    properties: UnifiTrafficRouteNodeProperties = UnifiTrafficRouteNodeProperties()
    sub_resource_relationship: UnifiTrafficRouteToSiteRel = UnifiTrafficRouteToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiTrafficRouteToClientRel(),
        ],
    )
