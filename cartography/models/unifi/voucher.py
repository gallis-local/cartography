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
class UnifiVoucherNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    code: PropertyRef = PropertyRef("code", extra_index=True)
    note: PropertyRef = PropertyRef("note")
    quota: PropertyRef = PropertyRef("quota")
    duration: PropertyRef = PropertyRef("duration")
    qos_overwrite: PropertyRef = PropertyRef("qos_overwrite")
    qos_usage_quota: PropertyRef = PropertyRef("qos_usage_quota")
    qos_rate_max_up: PropertyRef = PropertyRef("qos_rate_max_up")
    qos_rate_max_down: PropertyRef = PropertyRef("qos_rate_max_down")
    used: PropertyRef = PropertyRef("used")
    create_time: PropertyRef = PropertyRef("create_time")
    start_time: PropertyRef = PropertyRef("start_time")
    end_time: PropertyRef = PropertyRef("end_time")
    for_hotspot: PropertyRef = PropertyRef("for_hotspot")
    admin_name: PropertyRef = PropertyRef("admin_name")
    status: PropertyRef = PropertyRef("status")
    status_expires: PropertyRef = PropertyRef("status_expires")
    site_id: PropertyRef = PropertyRef("SITE_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiVoucherToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiVoucherToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SITE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiVoucherToSiteRelProperties = UnifiVoucherToSiteRelProperties()


@dataclass(frozen=True)
class UnifiVoucherSchema(CartographyNodeSchema):
    label: str = "UnifiVoucher"
    properties: UnifiVoucherNodeProperties = UnifiVoucherNodeProperties()
    sub_resource_relationship: UnifiVoucherToSiteRel = UnifiVoucherToSiteRel()
