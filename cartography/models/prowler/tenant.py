from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class ProwlerTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable Prowler tenant identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Prowler tenant was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Display name of the Prowler tenant.",
    )
    api_url: PropertyRef = PropertyRef(
        "api_url",
        description=(
            "Base URL of the Prowler Cloud or self-hosted Prowler API that "
            "served this tenant."
        ),
    )
    # The API's tenant resource exposes only `name`; it carries no timestamps.


@dataclass(frozen=True)
class ProwlerTenantSchema(CartographyNodeSchema):
    """A Prowler tenant whose scans and security findings are ingested by Cartography."""

    label: str = "ProwlerTenant"
    properties: ProwlerTenantNodeProperties = ProwlerTenantNodeProperties()
    sub_resource_relationship: None = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    scoped_cleanup: bool = False
