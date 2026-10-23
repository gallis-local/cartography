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
from cartography.models.unifi.extra_labels import NETWORK_SECURITY_POLICY


@dataclass(frozen=True)
class UnifiDPIAppNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiDPIApp."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    blocked: PropertyRef = PropertyRef("blocked", description="Blocked.")
    enabled: PropertyRef = PropertyRef("enabled", description="Enabled.")
    log: PropertyRef = PropertyRef("log", description="Log.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiDPIAppToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiDPIAppToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiDPIApp)
class UnifiDPIAppToSiteRel(CartographyRelSchema):
    """Relationship: UnifiDPIAppToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiDPIAppToSiteRelProperties = UnifiDPIAppToSiteRelProperties()


@dataclass(frozen=True)
class UnifiDPIAppSchema(CartographyNodeSchema):
    """A UnifiDPIApp."""

    label: str = "UnifiDPIApp"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_SECURITY_POLICY])
    properties: UnifiDPIAppNodeProperties = UnifiDPIAppNodeProperties()
    sub_resource_relationship: UnifiDPIAppToSiteRel = UnifiDPIAppToSiteRel()
