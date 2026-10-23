from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class FleetDMTenantNodeProperties(CartographyNodeProperties):
    """Properties of a FleetDMTenant node."""

    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this resource in Fleet."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Name of the resource.")
    base_url: PropertyRef = PropertyRef(
        "base_url", description="Base URL of the Fleet instance this tenant represents."
    )


@dataclass(frozen=True)
class FleetDMTenantSchema(CartographyNodeSchema):
    """A Fleet instance being ingested. The root node of the FleetDM module."""

    label: str = "FleetDMTenant"
    properties: FleetDMTenantNodeProperties = FleetDMTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
