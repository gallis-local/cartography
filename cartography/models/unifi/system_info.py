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
class UnifiSystemInfoNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    anonymous_controller_id: PropertyRef = PropertyRef(
        "anonymous_controller_id", extra_index=True
    )
    hostname: PropertyRef = PropertyRef("hostname")
    name: PropertyRef = PropertyRef("name")
    version: PropertyRef = PropertyRef("version")
    previous_version: PropertyRef = PropertyRef("previous_version")
    update_available: PropertyRef = PropertyRef("update_available")
    ip_addrs: PropertyRef = PropertyRef("ip_addrs")
    is_cloud_console: PropertyRef = PropertyRef("is_cloud_console")
    ubnt_device_type: PropertyRef = PropertyRef("ubnt_device_type")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiSystemInfoToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:HAS_SYSTEM_INFO]->(:UnifiSystemInfo)
class UnifiSystemInfoToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SYSTEM_INFO"
    properties: UnifiSystemInfoToSiteRelProperties = (
        UnifiSystemInfoToSiteRelProperties()
    )


@dataclass(frozen=True)
class UnifiSystemInfoSchema(CartographyNodeSchema):
    label: str = "UnifiSystemInfo"
    properties: UnifiSystemInfoNodeProperties = UnifiSystemInfoNodeProperties()
    sub_resource_relationship: UnifiSystemInfoToSiteRel = UnifiSystemInfoToSiteRel()
