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
class UnifiDPIGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    attr_no_delete: PropertyRef = PropertyRef("attr_no_delete")
    attr_hidden_id: PropertyRef = PropertyRef("attr_hidden_id")


@dataclass(frozen=True)
class UnifiDPIGroupToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)<-[:RESOURCE]-(:UnifiDPIGroup)
class UnifiDPIGroupToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiDPIGroupToSiteRelProperties = UnifiDPIGroupToSiteRelProperties()


@dataclass(frozen=True)
class UnifiDPIGroupSchema(CartographyNodeSchema):
    label: str = "UnifiDPIGroup"
    properties: UnifiDPIGroupNodeProperties = UnifiDPIGroupNodeProperties()
    sub_resource_relationship: UnifiDPIGroupToSiteRel = UnifiDPIGroupToSiteRel()
