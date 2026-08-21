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
from cartography.models.unifi.extra_labels import NETWORK_PERFORMANCE_TEST


@dataclass(frozen=True)
class UnifiSpeedtestNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiSpeedtest."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    download: PropertyRef = PropertyRef("download", description="Download.")
    upload: PropertyRef = PropertyRef("upload", description="Upload.")
    ping: PropertyRef = PropertyRef("ping", description="Ping.")
    timestamp: PropertyRef = PropertyRef("timestamp", description="Timestamp.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiSpeedtestToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiSpeedtestToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiSpeedtest)
class UnifiSpeedtestToSiteRel(CartographyRelSchema):
    """Relationship: UnifiSpeedtestToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiSpeedtestToSiteRelProperties = UnifiSpeedtestToSiteRelProperties()


@dataclass(frozen=True)
class UnifiSpeedtestToDeviceRelProperties(CartographyRelProperties):
    """Properties of the UnifiSpeedtestToDevice relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSpeedtest)-[:MEASURED_BY]->(:UnifiDevice) (gateway device)
class UnifiSpeedtestToDeviceRel(CartographyRelSchema):
    """Relationship: UnifiSpeedtestToDevice."""

    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gateway_mac")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEASURED_BY"
    properties: UnifiSpeedtestToDeviceRelProperties = (
        UnifiSpeedtestToDeviceRelProperties()
    )


@dataclass(frozen=True)
class UnifiSpeedtestSchema(CartographyNodeSchema):
    """A UnifiSpeedtest."""

    label: str = "UnifiSpeedtest"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_PERFORMANCE_TEST])
    properties: UnifiSpeedtestNodeProperties = UnifiSpeedtestNodeProperties()
    sub_resource_relationship: UnifiSpeedtestToSiteRel = UnifiSpeedtestToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiSpeedtestToDeviceRel(),
        ],
    )
