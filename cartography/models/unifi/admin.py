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
class UnifiAdminNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    role: PropertyRef = PropertyRef("role")
    is_super_admin: PropertyRef = PropertyRef("is_super_admin")
    last_site_name: PropertyRef = PropertyRef("last_site_name")
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiAdminToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiAdmin)
class UnifiAdminToSiteRel(CartographyRelSchema):
    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiAdminToSiteRelProperties = UnifiAdminToSiteRelProperties()


@dataclass(frozen=True)
class UnifiAdminToUserAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiAdmin)-[:HAS_ACCOUNT]->(:UserAccount) via email
class UnifiAdminToUserAccountRel(CartographyRelSchema):
    target_node_label: str = "UserAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCOUNT"
    properties: UnifiAdminToUserAccountRelProperties = (
        UnifiAdminToUserAccountRelProperties()
    )


@dataclass(frozen=True)
class UnifiAdminSchema(CartographyNodeSchema):
    label: str = "UnifiAdmin"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: UnifiAdminNodeProperties = UnifiAdminNodeProperties()
    sub_resource_relationship: UnifiAdminToSiteRel = UnifiAdminToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiAdminToUserAccountRel(),
        ],
    )
