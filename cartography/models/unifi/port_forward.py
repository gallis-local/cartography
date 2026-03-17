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
class UnifiPortForwardNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    enabled: PropertyRef = PropertyRef("enabled")
    destination_port: PropertyRef = PropertyRef("destination_port")
    forward_port: PropertyRef = PropertyRef("forward_port")
    forward_ip: PropertyRef = PropertyRef("forward_ip")
    protocol: PropertyRef = PropertyRef("protocol")
    interface: PropertyRef = PropertyRef("interface")
    source: PropertyRef = PropertyRef("source")


@dataclass(frozen=True)
class UnifiPortForwardToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiPortForward)
class UnifiPortForwardToSiteRel(CartographyRelSchema):
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
    label: str = "UnifiPortForward"
    properties: UnifiPortForwardNodeProperties = UnifiPortForwardNodeProperties()
    sub_resource_relationship: UnifiPortForwardToSiteRel = UnifiPortForwardToSiteRel()
