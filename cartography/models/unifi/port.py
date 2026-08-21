from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.unifi.extra_labels import NETWORK_INTERFACE


@dataclass(frozen=True)
class UnifiPortNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiPort."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    port_idx: PropertyRef = PropertyRef("port_idx", description="Port idx.")
    name: PropertyRef = PropertyRef("name", description="Name.")
    port_poe: PropertyRef = PropertyRef("port_poe", description="Port poe.")
    poe_enable: PropertyRef = PropertyRef("poe_enable", description="Poe enable.")
    poe_mode: PropertyRef = PropertyRef("poe_mode", description="Poe mode.")
    poe_voltage: PropertyRef = PropertyRef("poe_voltage", description="Poe voltage.")
    portconf_id: PropertyRef = PropertyRef("portconf_id", description="Portconf id.")
    up: PropertyRef = PropertyRef("up", description="Up.")
    speed: PropertyRef = PropertyRef("speed", description="Speed.")
    full_duplex: PropertyRef = PropertyRef("full_duplex", description="Full duplex.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiPortToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiPortToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiPort)
class UnifiPortToSiteRel(CartographyRelSchema):
    """Relationship: UnifiPortToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiPortToSiteRelProperties = UnifiPortToSiteRelProperties()


@dataclass(frozen=True)
class UnifiPortToDeviceRelProperties(CartographyRelProperties):
    """Properties of the UnifiPortToDevice relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiDevice)-[:HAS_PORT]->(:UnifiPort)
class UnifiPortToDeviceRel(CartographyRelSchema):
    """Relationship: UnifiPortToDevice."""

    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_mac")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PORT"
    properties: UnifiPortToDeviceRelProperties = UnifiPortToDeviceRelProperties()


@dataclass(frozen=True)
class UnifiPortSchema(CartographyNodeSchema):
    """A UnifiPort."""

    label: str = "UnifiPort"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_INTERFACE])
    properties: UnifiPortNodeProperties = UnifiPortNodeProperties()
    sub_resource_relationship: UnifiPortToSiteRel = UnifiPortToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiPortToDeviceRel(),
        ],
    )
