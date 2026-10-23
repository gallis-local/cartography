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
from cartography.models.unifi.extra_labels import NETWORK_ACCESS_POINT


@dataclass(frozen=True)
class UnifiWlanNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiWlan."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Name.")
    enabled: PropertyRef = PropertyRef("enabled", description="Enabled.")
    is_guest: PropertyRef = PropertyRef("is_guest", description="Is guest.")
    security: PropertyRef = PropertyRef("security", description="Security.")
    wpa_mode: PropertyRef = PropertyRef("wpa_mode", description="Wpa mode.")
    wpa_enc: PropertyRef = PropertyRef("wpa_enc", description="Wpa enc.")
    usergroup_id: PropertyRef = PropertyRef("usergroup_id", description="Usergroup id.")
    hide_ssid: PropertyRef = PropertyRef("hide_ssid", description="Hide ssid.")
    mac_filter_enabled: PropertyRef = PropertyRef(
        "mac_filter_enabled", description="Mac filter enabled."
    )
    mac_filter_policy: PropertyRef = PropertyRef(
        "mac_filter_policy", description="Mac filter policy."
    )
    bc_filter_enabled: PropertyRef = PropertyRef(
        "bc_filter_enabled", description="Bc filter enabled."
    )
    no2ghz_oui: PropertyRef = PropertyRef("no2ghz_oui", description="No2ghz oui.")
    name_combine_enabled: PropertyRef = PropertyRef(
        "name_combine_enabled", description="Name combine enabled."
    )
    wlangroup_id: PropertyRef = PropertyRef("wlangroup_id", description="Wlangroup id.")
    schedule: PropertyRef = PropertyRef("schedule", description="Schedule.")
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiWlanToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiWlanToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiWlan)
class UnifiWlanToSiteRel(CartographyRelSchema):
    """Relationship: UnifiWlanToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiWlanToSiteRelProperties = UnifiWlanToSiteRelProperties()


@dataclass(frozen=True)
class UnifiWlanSchema(CartographyNodeSchema):
    """A UnifiWlan."""

    label: str = "UnifiWlan"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ACCESS_POINT])
    properties: UnifiWlanNodeProperties = UnifiWlanNodeProperties()
    sub_resource_relationship: UnifiWlanToSiteRel = UnifiWlanToSiteRel()
