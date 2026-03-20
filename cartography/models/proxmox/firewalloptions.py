"""
Data models for Proxmox firewall global options.

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher

# ProxmoxFirewallOptions Node Schema

@dataclass(frozen=True)
class ProxmoxFirewallOptionsNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxFirewallOptions node.

    Represents firewall global configuration options at cluster or node level.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    scope: PropertyRef = PropertyRef("scope")
    scope_id: PropertyRef = PropertyRef("scope_id")
    node_id: PropertyRef = PropertyRef("node_id")
    enable: PropertyRef = PropertyRef("enable")
    policy_in: PropertyRef = PropertyRef("policy_in")
    policy_out: PropertyRef = PropertyRef("policy_out")
    log_level_in: PropertyRef = PropertyRef("log_level_in")
    log_level_out: PropertyRef = PropertyRef("log_level_out")
    nf_conntrack_max: PropertyRef = PropertyRef("nf_conntrack_max")
    nf_conntrack_tcp_timeout_established: PropertyRef = PropertyRef("nf_conntrack_tcp_timeout_established")

@dataclass(frozen=True)
class ProxmoxFirewallOptionsToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxFirewallOptionsToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxFirewallOptions)

    Firewall options belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxFirewallOptionsToClusterRelProperties = (
        ProxmoxFirewallOptionsToClusterRelProperties()
    )

@dataclass(frozen=True)
class ProxmoxFirewallOptionsToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class ProxmoxFirewallOptionsToNodeRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxFirewallOptions)-[:APPLIES_TO_NODE]->(:ProxmoxNode)

    Node-level firewall options apply to a specific node.
    Only created when scope == "node".
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("node_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO_NODE"
    properties: ProxmoxFirewallOptionsToNodeRelProperties = (
        ProxmoxFirewallOptionsToNodeRelProperties()
    )

@dataclass(frozen=True)
class ProxmoxFirewallOptionsSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxFirewallOptions.

    Global firewall configuration options.
    """

    label: str = "ProxmoxFirewallOptions"
    properties: ProxmoxFirewallOptionsNodeProperties = ProxmoxFirewallOptionsNodeProperties()
    sub_resource_relationship: ProxmoxFirewallOptionsToClusterRel = (
        ProxmoxFirewallOptionsToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxFirewallOptionsToNodeRel(),
        ]
    )
