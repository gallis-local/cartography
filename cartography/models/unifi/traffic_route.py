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
from cartography.models.unifi.extra_labels import NETWORK_ROUTING_RULE


@dataclass(frozen=True)
class UnifiTrafficRouteNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiTrafficRoute."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    description: PropertyRef = PropertyRef("description", description="Description.")
    enabled: PropertyRef = PropertyRef("enabled", description="Enabled.")
    matching_target: PropertyRef = PropertyRef(
        "matching_target", description="Matching target."
    )
    network_id: PropertyRef = PropertyRef("network_id", description="Network id.")
    next_hop: PropertyRef = PropertyRef("next_hop", description="Next hop.")
    regions: PropertyRef = PropertyRef("regions", description="Regions.")
    domains: PropertyRef = PropertyRef("domains", description="Domains.")
    target_client_macs: PropertyRef = PropertyRef(
        "target_client_macs", description="Target client macs."
    )
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiTrafficRouteToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiTrafficRouteToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiTrafficRoute)
class UnifiTrafficRouteToSiteRel(CartographyRelSchema):
    """Relationship: UnifiTrafficRouteToSite."""

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
    """Properties of the UnifiTrafficRouteToClient relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiTrafficRoute)-[:APPLIES_TO_CLIENT]->(:UnifiClient)
class UnifiTrafficRouteToClientRel(CartographyRelSchema):
    """Relationship: UnifiTrafficRouteToClient."""

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
    """A UnifiTrafficRoute."""

    label: str = "UnifiTrafficRoute"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ROUTING_RULE])
    properties: UnifiTrafficRouteNodeProperties = UnifiTrafficRouteNodeProperties()
    sub_resource_relationship: UnifiTrafficRouteToSiteRel = UnifiTrafficRouteToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiTrafficRouteToClientRel(),
        ],
    )
