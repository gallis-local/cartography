"""
Data models for Proxmox firewall configurations.

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher

# ============================================================================
# ProxmoxFirewallRule Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxFirewallRuleNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxFirewallRule node.

    Represents firewall rules at cluster, node, or VM level.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    scope: PropertyRef = PropertyRef("scope", extra_index=True)  # cluster, node, vm
    scope_id: PropertyRef = PropertyRef("scope_id")  # node name or vmid if applicable
    pos: PropertyRef = PropertyRef(
        "pos", extra_index=True
    )  # Position for rule ordering
    type: PropertyRef = PropertyRef("type")  # in, out, group
    action: PropertyRef = PropertyRef(
        "action", extra_index=True
    )  # ACCEPT, DROP, REJECT
    enable: PropertyRef = PropertyRef("enable", extra_index=True)
    iface: PropertyRef = PropertyRef("iface")  # Network interface
    source: PropertyRef = PropertyRef(
        "source", extra_index=True
    )  # Source address/network
    dest: PropertyRef = PropertyRef(
        "dest", extra_index=True
    )  # Destination address/network
    proto: PropertyRef = PropertyRef(
        "proto", extra_index=True
    )  # Protocol (tcp, udp, icmp)
    sport: PropertyRef = PropertyRef("sport")  # Source port(s)
    dport: PropertyRef = PropertyRef("dport", extra_index=True)  # Destination port(s)
    comment: PropertyRef = PropertyRef("comment")
    macro: PropertyRef = PropertyRef("macro")  # Predefined macro name
    log: PropertyRef = PropertyRef("log")  # Log level
    # IPSet references extracted from source/dest (prefixed with +)
    source_ipsets: PropertyRef = PropertyRef("source_ipsets")  # IPSets in source
    dest_ipsets: PropertyRef = PropertyRef("dest_ipsets")  # IPSets in dest


@dataclass(frozen=True)
class ProxmoxFirewallRuleToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxFirewallRule to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallRuleToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxFirewallRule)-[:RESOURCE]->(:ProxmoxCluster)

    Firewall rules belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxFirewallRuleToClusterRelProperties = (
        ProxmoxFirewallRuleToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxFirewallRuleSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxFirewallRule.

    Firewall rules controlling network traffic.
    """

    label: str = "ProxmoxFirewallRule"
    properties: ProxmoxFirewallRuleNodeProperties = ProxmoxFirewallRuleNodeProperties()
    sub_resource_relationship: ProxmoxFirewallRuleToClusterRel = (
        ProxmoxFirewallRuleToClusterRel()
    )


# ============================================================================
# ProxmoxFirewallIPSet Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxFirewallIPSetNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxFirewallIPSet node.

    Represents IP sets (address groups) used in firewall rules.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    scope: PropertyRef = PropertyRef("scope")  # cluster, node, vm
    scope_id: PropertyRef = PropertyRef("scope_id")
    comment: PropertyRef = PropertyRef("comment")
    cidrs: PropertyRef = PropertyRef("cidrs")  # Array of CIDR entries


@dataclass(frozen=True)
class ProxmoxFirewallIPSetToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxFirewallIPSet to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallIPSetToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxFirewallIPSet)-[:RESOURCE]->(:ProxmoxCluster)

    IP sets belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxFirewallIPSetToClusterRelProperties = (
        ProxmoxFirewallIPSetToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxFirewallIPSetSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxFirewallIPSet.

    IP address sets for use in firewall rules.
    """

    label: str = "ProxmoxFirewallIPSet"
    properties: ProxmoxFirewallIPSetNodeProperties = (
        ProxmoxFirewallIPSetNodeProperties()
    )
    sub_resource_relationship: ProxmoxFirewallIPSetToClusterRel = (
        ProxmoxFirewallIPSetToClusterRel()
    )


# ============================================================================
# MatchLink Schemas for Firewall Relationships
# ============================================================================
# These MatchLinks connect firewall rules to their scope (nodes/VMs) and IPSets.


@dataclass(frozen=True)
class ProxmoxFirewallRuleToNodeMatchLinkProperties(CartographyRelProperties):
    """
    Properties for firewall rule to node APPLIES_TO_NODE relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallRuleToNodeMatchLink(CartographyRelSchema):
    """
    MatchLink: (:ProxmoxFirewallRule)-[:APPLIES_TO_NODE]->(:ProxmoxNode)

    Connects node-scoped firewall rules to the nodes they apply to.
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("scope_id"),  # Node ID/name
        }
    )
    source_node_label: str = "ProxmoxFirewallRule"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO_NODE"
    properties: ProxmoxFirewallRuleToNodeMatchLinkProperties = (
        ProxmoxFirewallRuleToNodeMatchLinkProperties()
    )


@dataclass(frozen=True)
class ProxmoxFirewallRuleToVMMatchLinkProperties(CartographyRelProperties):
    """
    Properties for firewall rule to VM APPLIES_TO_VM relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallRuleToVMMatchLink(CartographyRelSchema):
    """
    MatchLink: (:ProxmoxFirewallRule)-[:APPLIES_TO_VM]->(:ProxmoxVM)

    Connects VM-scoped firewall rules to the VMs they apply to.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid_int"),  # Integer VMID
        }
    )
    source_node_label: str = "ProxmoxFirewallRule"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO_VM"
    properties: ProxmoxFirewallRuleToVMMatchLinkProperties = (
        ProxmoxFirewallRuleToVMMatchLinkProperties()
    )


@dataclass(frozen=True)
class ProxmoxFirewallRuleToIPSetMatchLinkProperties(CartographyRelProperties):
    """
    Properties for firewall rule to IPSet USES_IPSET relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Usage context
    in_source: PropertyRef = PropertyRef("in_source")  # IPSet used in source field
    in_dest: PropertyRef = PropertyRef("in_dest")  # IPSet used in dest field


@dataclass(frozen=True)
class ProxmoxFirewallRuleToIPSetMatchLink(CartographyRelSchema):
    """
    MatchLink: (:ProxmoxFirewallRule)-[:USES_IPSET]->(:ProxmoxFirewallIPSet)

    Connects firewall rules to the IPSets they reference in source/dest fields.
    """

    target_node_label: str = "ProxmoxFirewallIPSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("ipset_name"),
            "scope": PropertyRef("scope"),
        }
    )
    source_node_label: str = "ProxmoxFirewallRule"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_IPSET"
    properties: ProxmoxFirewallRuleToIPSetMatchLinkProperties = (
        ProxmoxFirewallRuleToIPSetMatchLinkProperties()
    )
