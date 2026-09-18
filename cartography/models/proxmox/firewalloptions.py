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

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this firewall options object, derived from the scope it applies to.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    scope: PropertyRef = PropertyRef(
        "scope", description="Level these options apply at: `cluster`, `node` or `vm`."
    )
    scope_id: PropertyRef = PropertyRef(
        "scope_id",
        description="Identifier of the object the options apply to. Null for cluster-level options.",
    )
    node_id: PropertyRef = PropertyRef(
        "node_id",
        description="Id of the `ProxmoxNode` these options apply to. Null for cluster- and guest-level options.",
    )
    enable: PropertyRef = PropertyRef(
        "enable",
        description="True when the firewall is switched on at this level. With it off, no rules at this level are enforced.",
    )
    policy_in: PropertyRef = PropertyRef(
        "policy_in",
        description="Default action for inbound traffic that no rule matches: `ACCEPT`, `REJECT` or `DROP`.",
    )
    policy_out: PropertyRef = PropertyRef(
        "policy_out",
        description="Default action for outbound traffic that no rule matches: `ACCEPT`, `REJECT` or `DROP`.",
    )
    log_level_in: PropertyRef = PropertyRef(
        "log_level_in",
        description="Log level applied to packets handled by the inbound default policy, e.g. `nolog` or `info`.",
    )
    log_level_out: PropertyRef = PropertyRef(
        "log_level_out",
        description="Log level applied to packets handled by the outbound default policy, e.g. `nolog` or `info`.",
    )
    nf_conntrack_max: PropertyRef = PropertyRef(
        "nf_conntrack_max",
        description="Maximum number of entries the node's connection tracking table may hold.",
    )
    nf_conntrack_tcp_timeout_established: PropertyRef = PropertyRef(
        "nf_conntrack_tcp_timeout_established",
        description="Seconds an established TCP connection stays in the connection tracking table without traffic.",
    )


@dataclass(frozen=True)
class ProxmoxFirewallOptionsToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallOptionsToClusterRel(CartographyRelSchema):
    """
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
    properties: ProxmoxFirewallOptionsNodeProperties = (
        ProxmoxFirewallOptionsNodeProperties()
    )
    sub_resource_relationship: ProxmoxFirewallOptionsToClusterRel = (
        ProxmoxFirewallOptionsToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxFirewallOptionsToNodeRel(),
        ]
    )
