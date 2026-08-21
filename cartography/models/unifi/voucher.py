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
from cartography.models.unifi.extra_labels import NETWORK_GUEST_ACCESS


@dataclass(frozen=True)
class UnifiVoucherNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiVoucher."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    code: PropertyRef = PropertyRef("code", extra_index=True, description="Code.")
    note: PropertyRef = PropertyRef("note", description="Note.")
    quota: PropertyRef = PropertyRef("quota", description="Quota.")
    duration: PropertyRef = PropertyRef("duration", description="Duration.")
    qos_overwrite: PropertyRef = PropertyRef(
        "qos_overwrite", description="Qos overwrite."
    )
    qos_usage_quota: PropertyRef = PropertyRef(
        "qos_usage_quota", description="Qos usage quota."
    )
    qos_rate_max_up: PropertyRef = PropertyRef(
        "qos_rate_max_up", description="Qos rate max up."
    )
    qos_rate_max_down: PropertyRef = PropertyRef(
        "qos_rate_max_down", description="Qos rate max down."
    )
    used: PropertyRef = PropertyRef("used", description="Used.")
    create_time: PropertyRef = PropertyRef("create_time", description="Create time.")
    start_time: PropertyRef = PropertyRef("start_time", description="Start time.")
    end_time: PropertyRef = PropertyRef("end_time", description="End time.")
    for_hotspot: PropertyRef = PropertyRef("for_hotspot", description="For hotspot.")
    admin_name: PropertyRef = PropertyRef("admin_name", description="Admin name.")
    status: PropertyRef = PropertyRef("status", description="Status.")
    status_expires: PropertyRef = PropertyRef(
        "status_expires", description="Status expires."
    )
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiVoucherToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiVoucherToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiVoucher)
class UnifiVoucherToSiteRel(CartographyRelSchema):
    """Relationship: UnifiVoucherToSite."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiVoucherToSiteRelProperties = UnifiVoucherToSiteRelProperties()


@dataclass(frozen=True)
class UnifiVoucherSchema(CartographyNodeSchema):
    """A UnifiVoucher."""

    label: str = "UnifiVoucher"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_GUEST_ACCESS])
    properties: UnifiVoucherNodeProperties = UnifiVoucherNodeProperties()
    sub_resource_relationship: UnifiVoucherToSiteRel = UnifiVoucherToSiteRel()
