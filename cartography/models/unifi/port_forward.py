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
from cartography.models.unifi.extra_labels import NETWORK_ADDRESS_TRANSLATION


@dataclass(frozen=True)
class UnifiPortForwardNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiPortForward."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    name: PropertyRef = PropertyRef("name", description="Name.")
    enabled: PropertyRef = PropertyRef("enabled", description="Enabled.")
    destination_port: PropertyRef = PropertyRef(
        "destination_port", description="Destination port."
    )
    forward_port: PropertyRef = PropertyRef("forward_port", description="Forward port.")
    forward_ip: PropertyRef = PropertyRef("forward_ip", description="Forward ip.")
    protocol: PropertyRef = PropertyRef("protocol", description="Protocol.")
    interface: PropertyRef = PropertyRef("interface", description="Interface.")
    source: PropertyRef = PropertyRef("source", description="Source.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiPortForwardToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiPortForwardToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiPortForward)
class UnifiPortForwardToSiteRel(CartographyRelSchema):
    """Relationship: UnifiPortForwardToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiPortForwardToSiteRelProperties = (
        UnifiPortForwardToSiteRelProperties()
    )


@dataclass(frozen=True)
class UnifiPortForwardSchema(CartographyNodeSchema):
    """A UnifiPortForward."""

    label: str = "UnifiPortForward"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ADDRESS_TRANSLATION])
    properties: UnifiPortForwardNodeProperties = UnifiPortForwardNodeProperties()
    sub_resource_relationship: UnifiPortForwardToSiteRel = UnifiPortForwardToSiteRel()
