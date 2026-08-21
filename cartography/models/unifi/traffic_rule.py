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
from cartography.models.unifi.extra_labels import NETWORK_ROUTING_RULE


@dataclass(frozen=True)
class UnifiTrafficRuleNodeProperties(CartographyNodeProperties):
    """Properties of a UnifiTrafficRule."""

    id: PropertyRef = PropertyRef("id", description="Id.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )
    description: PropertyRef = PropertyRef("description", description="Description.")
    enabled: PropertyRef = PropertyRef("enabled", description="Enabled.")
    action: PropertyRef = PropertyRef("action", description="Action.")
    matching_target: PropertyRef = PropertyRef(
        "matching_target", description="Matching target."
    )
    bandwidth_limit_enabled: PropertyRef = PropertyRef(
        "bandwidth_limit_enabled", description="Bandwidth limit enabled."
    )
    download_limit_kbps: PropertyRef = PropertyRef(
        "download_limit_kbps", description="Download limit kbps."
    )
    upload_limit_kbps: PropertyRef = PropertyRef(
        "upload_limit_kbps", description="Upload limit kbps."
    )
    app_ids: PropertyRef = PropertyRef("app_ids", description="App ids.")
    app_category_ids: PropertyRef = PropertyRef(
        "app_category_ids", description="App category ids."
    )
    network_ids: PropertyRef = PropertyRef("network_ids", description="Network ids.")
    domains: PropertyRef = PropertyRef("domains", description="Domains.")
    target_client_macs: PropertyRef = PropertyRef(
        "target_client_macs", description="Target client macs."
    )
    site_id: PropertyRef = PropertyRef(
        "site_id", set_in_kwargs=True, description="Site id."
    )


@dataclass(frozen=True)
class UnifiTrafficRuleToSiteRelProperties(CartographyRelProperties):
    """Properties of the UnifiTrafficRuleToSite relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiSite)-[:RESOURCE]->(:UnifiTrafficRule)
class UnifiTrafficRuleToSiteRel(CartographyRelSchema):
    """Relationship: UnifiTrafficRuleToSite."""

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
class UnifiTrafficRuleToDPIAppRelProperties(CartographyRelProperties):
    """Properties of the UnifiTrafficRuleToDPIApp relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiTrafficRule)-[:APPLIES_TO_APP]->(:UnifiDPIApp)
class UnifiTrafficRuleToDPIAppRel(CartographyRelSchema):
    """Relationship: UnifiTrafficRuleToDPIApp."""

    target_node_label: str = "UnifiDPIApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("app_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO_APP"
    properties: UnifiTrafficRuleToDPIAppRelProperties = (
        UnifiTrafficRuleToDPIAppRelProperties()
    )


@dataclass(frozen=True)
class UnifiTrafficRuleToClientRelProperties(CartographyRelProperties):
    """Properties of the UnifiTrafficRuleToClient relationship."""

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Lastupdated."
    )


@dataclass(frozen=True)
# (:UnifiTrafficRule)-[:APPLIES_TO_CLIENT]->(:UnifiClient)
class UnifiTrafficRuleToClientRel(CartographyRelSchema):
    """Relationship: UnifiTrafficRuleToClient."""

    target_node_label: str = "UnifiClient"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_client_macs", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO_CLIENT"
    properties: UnifiTrafficRuleToClientRelProperties = (
        UnifiTrafficRuleToClientRelProperties()
    )


@dataclass(frozen=True)
class UnifiTrafficRuleSchema(CartographyNodeSchema):
    """A UnifiTrafficRule."""

    label: str = "UnifiTrafficRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ROUTING_RULE])
    properties: UnifiTrafficRuleNodeProperties = UnifiTrafficRuleNodeProperties()
    sub_resource_relationship: UnifiTrafficRuleToSiteRel = UnifiTrafficRuleToSiteRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnifiTrafficRuleToDPIAppRel(),
            UnifiTrafficRuleToClientRel(),
        ],
    )
