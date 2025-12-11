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
class UnifiDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("mac")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    mac: PropertyRef = PropertyRef("mac")
    adopted: PropertyRef = PropertyRef("adopted")
    type: PropertyRef = PropertyRef("type")
    model: PropertyRef = PropertyRef("model")
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class UnifiDeviceToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)<-[:RESOURCE]-(:UnifiDevice)
class UnifiDeviceToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiDeviceToSiteRelProperties = UnifiDeviceToSiteRelProperties()


@dataclass(frozen=True)
class UnifiDeviceSchema(CartographyNodeSchema):
    label: str = "UnifiDevice"
    properties: UnifiDeviceNodeProperties = UnifiDeviceNodeProperties()
    sub_resource_relationship: UnifiDeviceToSiteRel = UnifiDeviceToSiteRel()
