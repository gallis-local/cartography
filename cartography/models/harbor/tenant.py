from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class HarborInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Lowercased host[:port] of the Harbor instance. This is also the registry host images are pulled from.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    url: PropertyRef = PropertyRef(
        "url", description="Base URL Cartography uses to reach the Harbor API."
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Harbor release reported by `/systeminfo`, e.g. `v2.11.0`.",
    )


@dataclass(frozen=True)
class HarborInstanceSchema(CartographyNodeSchema):
    """A Harbor registry instance, identified by the configured host.

    Ontology Mapping: The extra label `Tenant` enables cross-platform tenant queries.

    This is the sub-resource root of the module: every other Harbor node belongs to
    exactly one instance, so cleanup is scoped per instance and two Harbor instances
    can be synced side by side.
    """

    label: str = "HarborInstance"
    properties: HarborInstanceNodeProperties = HarborInstanceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class HarborResourceToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class HarborResourceToInstanceRel(CartographyRelSchema):
    """Contains a Harbor resource within its instance and scopes its cleanup."""

    target_node_label: str = "HarborInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: HarborResourceToInstanceRelProperties = (
        HarborResourceToInstanceRelProperties()
    )
