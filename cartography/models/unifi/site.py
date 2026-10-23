from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class UnifiSiteNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiSite."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    name: PropertyRef = PropertyRef("name", description="Name.")
    desc: PropertyRef = PropertyRef("desc", description="Desc.")
    role: PropertyRef = PropertyRef("role", description="Role.")
    host: PropertyRef = PropertyRef(
        "host",
        set_in_kwargs=True,
        description=(
            "Hostname of the UniFi controller this site belongs to. Used to scope "
            "site cleanup to the controller being synced, since UnifiSite is a root "
            "node with no sub-resource relationship and multiple controllers may be "
            "synced into the same graph."
        ),
    )


@dataclass(frozen=True)
class UnifiSiteSchema(CartographyNodeSchema):
    """A UnifiSite."""

    label: str = "UnifiSite"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    properties: UnifiSiteNodeProperties = UnifiSiteNodeProperties()
    scoped_cleanup: bool = False
