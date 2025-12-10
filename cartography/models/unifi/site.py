from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class UnifiSiteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    desc: PropertyRef = PropertyRef("desc")
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class UnifiSiteSchema(CartographyNodeSchema):
    label: str = "UnifiSite"
    properties: UnifiSiteNodeProperties = UnifiSiteNodeProperties()
