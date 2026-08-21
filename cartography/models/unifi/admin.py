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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class UnifiAdminNodeProperties(CartographyNodeProperties):
    """Properties of a UniFi controller administrator account."""

    id: PropertyRef = PropertyRef("id", description="Internal UniFi admin object ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Admin's display name.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Admin's email/login address."
    )
    role: PropertyRef = PropertyRef(
        "role", description="Admin role assigned on the site, e.g. admin, viewer."
    )
    is_super_admin: PropertyRef = PropertyRef(
        "is_super_admin",
        description="Whether this admin has super-admin (System Admin) privileges.",
    )
    last_site_name: PropertyRef = PropertyRef(
        "last_site_name", description="Name of the site the admin last accessed."
    )
    site_id: PropertyRef = PropertyRef("site_id", set_in_kwargs=True)


@dataclass(frozen=True)
class UnifiAdminToSiteRelProperties(CartographyRelProperties):
    """Properties of the relationship connecting a UnifiAdmin to its UnifiSite."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiAdmin)
class UnifiAdminToSiteRel(CartographyRelSchema):
    """Sub-resource relationship connecting a UnifiAdmin to the UnifiSite it administers."""

    target_node_label: str = "UnifiSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnifiAdminToSiteRelProperties = UnifiAdminToSiteRelProperties()


@dataclass(frozen=True)
class UnifiAdminToUserAccountRelProperties(CartographyRelProperties):
    """Properties of the relationship connecting a UnifiAdmin to its ontology UserAccount."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnifiAdmin)-[:HAS_ACCOUNT]->(:UserAccount) via email
class UnifiAdminToUserAccountRel(CartographyRelSchema):
    """Links a UnifiAdmin to the ontology UserAccount sharing its email address."""

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
    """A UniFi controller administrator account."""

    label: str = "UnifiAdmin"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: UnifiAdminNodeProperties = UnifiAdminNodeProperties()
    sub_resource_relationship: UnifiAdminToSiteRel = UnifiAdminToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiAdminToUserAccountRel(),
        ],
    )
