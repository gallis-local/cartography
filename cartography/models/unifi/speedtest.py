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


@dataclass(frozen=True)
class UnifiSpeedtestNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    interface_name: PropertyRef = PropertyRef("interface_name")
    download: PropertyRef = PropertyRef("download")
    upload: PropertyRef = PropertyRef("upload")
    ping: PropertyRef = PropertyRef("ping")
    timestamp: PropertyRef = PropertyRef("timestamp")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiSpeedtestToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiSpeedtest)
class UnifiSpeedtestToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiSpeedtestToSiteRelProperties = UnifiSpeedtestToSiteRelProperties()


@dataclass(frozen=True)
class UnifiSpeedtestToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSpeedtest)-[:MEASURED_BY]->(:UnifiDevice) (gateway device)
class UnifiSpeedtestToDeviceRel(CartographyRelSchema):
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
    label: str = "UnifiSpeedtest"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NetworkPerformanceTest"])
    properties: UnifiSpeedtestNodeProperties = UnifiSpeedtestNodeProperties()
    sub_resource_relationship: UnifiSpeedtestToSiteRel = UnifiSpeedtestToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiSpeedtestToDeviceRel(),
        ],
    )
