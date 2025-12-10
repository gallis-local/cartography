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
class UnifiClientNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("mac")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    is_guest: PropertyRef = PropertyRef("is_guest")
    mac: PropertyRef = PropertyRef("mac")
    ip: PropertyRef = PropertyRef("ip")
    oui: PropertyRef = PropertyRef("oui")
    satisfaction: PropertyRef = PropertyRef("satisfaction")
    channel: PropertyRef = PropertyRef("channel")
    radio: PropertyRef = PropertyRef("radio")
    is_wired: PropertyRef = PropertyRef("is_wired")
    qos_policy_applied: PropertyRef = PropertyRef("qos_policy_applied")


@dataclass(frozen=True)
class UnifiClientToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiDevice)<-[:RESOURCE]-(:UnifiClient)
class UnifiClientToDeviceRel(CartographyRelSchema):
    target_node_label: str = "UnifiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ap_mac")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiClientToDeviceRelProperties = UnifiClientToDeviceRelProperties()


@dataclass(frozen=True)
class UnifiClientSchema(CartographyNodeSchema):
    label: str = "UnifiClient"
    properties: UnifiClientNodeProperties = UnifiClientNodeProperties()
    sub_resource_relationship: UnifiClientToDeviceRel = UnifiClientToDeviceRel()
