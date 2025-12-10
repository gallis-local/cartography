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
class UnifiFirewallPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    enabled: PropertyRef = PropertyRef("enabled")
    action: PropertyRef = PropertyRef("action")
    protocol: PropertyRef = PropertyRef("protocol")
    predefined: PropertyRef = PropertyRef("predefined")
    index: PropertyRef = PropertyRef("index")
    connection_state_type: PropertyRef = PropertyRef("connection_state_type")
    logging: PropertyRef = PropertyRef("logging")


@dataclass(frozen=True)
class UnifiFirewallPolicyToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)<-[:RESOURCE]-(:UnifiFirewallPolicy)
class UnifiFirewallPolicyToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiFirewallPolicyToSiteRelProperties = UnifiFirewallPolicyToSiteRelProperties()


@dataclass(frozen=True)
class UnifiFirewallPolicySchema(CartographyNodeSchema):
    label: str = "UnifiFirewallPolicy"
    properties: UnifiFirewallPolicyNodeProperties = UnifiFirewallPolicyNodeProperties()
    sub_resource_relationship: UnifiFirewallPolicyToSiteRel = UnifiFirewallPolicyToSiteRel()
