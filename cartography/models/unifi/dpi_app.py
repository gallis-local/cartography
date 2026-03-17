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
class UnifiDPIAppNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    blocked: PropertyRef = PropertyRef("blocked")
    enabled: PropertyRef = PropertyRef("enabled")
    log: PropertyRef = PropertyRef("log")


@dataclass(frozen=True)
class UnifiDPIAppToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiDPIApp)
class UnifiDPIAppToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiDPIAppToSiteRelProperties = UnifiDPIAppToSiteRelProperties()


@dataclass(frozen=True)
class UnifiDPIAppSchema(CartographyNodeSchema):
    label: str = "UnifiDPIApp"
    properties: UnifiDPIAppNodeProperties = UnifiDPIAppNodeProperties()
    sub_resource_relationship: UnifiDPIAppToSiteRel = UnifiDPIAppToSiteRel()
