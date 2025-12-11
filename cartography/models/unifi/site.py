from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class UnifiSiteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    desc: PropertyRef = PropertyRef("desc")
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class UnifiSiteToSystemInfoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:HAS_SYSTEM_INFO]->(:UnifiSystemInfo)
class UnifiSiteToSystemInfoRel(CartographyRelSchema):
    target_node_label: str = "UnifiSystemInfo"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"site_id": PropertyRef("_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SYSTEM_INFO"
    properties: UnifiSiteToSystemInfoRelProperties = UnifiSiteToSystemInfoRelProperties()


@dataclass(frozen=True)
class UnifiSiteSchema(CartographyNodeSchema):
    label: str = "UnifiSite"
    properties: UnifiSiteNodeProperties = UnifiSiteNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiSiteToSystemInfoRel(),
        ],
    )
