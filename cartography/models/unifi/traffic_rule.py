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
class UnifiTrafficRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    description: PropertyRef = PropertyRef("description")
    enabled: PropertyRef = PropertyRef("enabled")
    action: PropertyRef = PropertyRef("action")
    matching_target: PropertyRef = PropertyRef("matching_target")
    # Bandwidth limit settings
    bandwidth_limit_enabled: PropertyRef = PropertyRef("bandwidth_limit_enabled")
    download_limit_kbps: PropertyRef = PropertyRef("download_limit_kbps")
    upload_limit_kbps: PropertyRef = PropertyRef("upload_limit_kbps")


@dataclass(frozen=True)
class UnifiTrafficRuleToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)<-[:RESOURCE]-(:UnifiTrafficRule)
class UnifiTrafficRuleToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiTrafficRuleToSiteRelProperties = (
        UnifiTrafficRuleToSiteRelProperties()
    )


@dataclass(frozen=True)
class UnifiTrafficRuleSchema(CartographyNodeSchema):
    label: str = "UnifiTrafficRule"
    properties: UnifiTrafficRuleNodeProperties = UnifiTrafficRuleNodeProperties()
    sub_resource_relationship: UnifiTrafficRuleToSiteRel = UnifiTrafficRuleToSiteRel()
