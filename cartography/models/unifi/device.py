from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


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
class UnifiDeviceSchema(CartographyNodeSchema):
    label: str = "UnifiDevice"
    properties: UnifiDeviceNodeProperties = UnifiDeviceNodeProperties()
