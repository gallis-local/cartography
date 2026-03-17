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
class UnifiWlanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    enabled: PropertyRef = PropertyRef("enabled")
    is_guest: PropertyRef = PropertyRef("is_guest")
    security: PropertyRef = PropertyRef("security")
    wpa_mode: PropertyRef = PropertyRef("wpa_mode")
    wpa_enc: PropertyRef = PropertyRef("wpa_enc")
    usergroup_id: PropertyRef = PropertyRef("usergroup_id")
    hide_ssid: PropertyRef = PropertyRef("hide_ssid")
    mac_filter_enabled: PropertyRef = PropertyRef("mac_filter_enabled")
    mac_filter_policy: PropertyRef = PropertyRef("mac_filter_policy")
    bc_filter_enabled: PropertyRef = PropertyRef("bc_filter_enabled")
    no2ghz_oui: PropertyRef = PropertyRef("no2ghz_oui")
    name_combine_enabled: PropertyRef = PropertyRef("name_combine_enabled")
    wlangroup_id: PropertyRef = PropertyRef("wlangroup_id")
    schedule: PropertyRef = PropertyRef("schedule")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiWlanToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)<-[:RESOURCE]-(:UnifiWlan)
class UnifiWlanToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiWlanToSiteRelProperties = UnifiWlanToSiteRelProperties()


@dataclass(frozen=True)
class UnifiWlanSchema(CartographyNodeSchema):
    label: str = "UnifiWlan"
    properties: UnifiWlanNodeProperties = UnifiWlanNodeProperties()
    sub_resource_relationship: UnifiWlanToSiteRel = UnifiWlanToSiteRel()
