from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class UnifiSiteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    desc: PropertyRef = PropertyRef("desc")
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class UnifiSiteSchema(CartographyNodeSchema):
    label: str = "UnifiSite"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    properties: UnifiSiteNodeProperties = UnifiSiteNodeProperties()
    scoped_cleanup: bool = False
