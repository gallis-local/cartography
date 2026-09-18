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

# ProxmoxFirewallRule Node Schema


@dataclass(frozen=True)
class ProxmoxFirewallRuleNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxFirewallRule node.

    Represents firewall rules at cluster, node, or VM level.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this rule, combining the scope it is defined at with its position in the chain.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    scope: PropertyRef = PropertyRef(
        "scope",
        extra_index=True,
        description="Level the rule is defined at: `cluster`, `node` or `vm`.",
    )
    scope_id: PropertyRef = PropertyRef(
        "scope_id",
        description="Id of the object owning the rule at that scope, i.e. the node id or guest id. Null for cluster-level rules.",
    )
    pos: PropertyRef = PropertyRef(
        "pos",
        extra_index=True,
        description="Zero-based position of the rule in its chain. Proxmox evaluates rules in this order.",
    )
    type: PropertyRef = PropertyRef(
        "type", description="Chain the rule belongs to: `in`, `out` or `group`."
    )
    action: PropertyRef = PropertyRef(
        "action",
        extra_index=True,
        description="What happens to a matching packet: `ACCEPT`, `DROP`, `REJECT`, or the name of a security group to jump to.",
    )
    enable: PropertyRef = PropertyRef(
        "enable",
        extra_index=True,
        description="True when the rule is active. A disabled rule keeps its position but is not evaluated.",
    )
    iface: PropertyRef = PropertyRef(
        "iface",
        description="Interface the rule is restricted to, e.g. `net0` on a guest or `vmbr0` on a node. Null matches any interface.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        extra_index=True,
        description="Source the rule matches: an address, a CIDR, a range, or `+name` to reference an IP set. Null matches any source.",
    )
    dest: PropertyRef = PropertyRef(
        "dest",
        extra_index=True,
        description="Destination the rule matches, in the same forms as `source`. Null matches any destination.",
    )
    proto: PropertyRef = PropertyRef(
        "proto",
        extra_index=True,
        description="IP protocol matched, e.g. `tcp`, `udp` or `icmp`. Null matches any protocol.",
    )
    sport: PropertyRef = PropertyRef(
        "sport",
        description="Source port or port range matched, e.g. `1024:65535`. Null matches any source port.",
    )
    dport: PropertyRef = PropertyRef(
        "dport",
        extra_index=True,
        description="Destination port matched: a port, a range, a service name, or a comma-separated list. Null matches any destination port.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment stored on the rule."
    )
    macro: PropertyRef = PropertyRef(
        "macro",
        description="Proxmox firewall macro the rule uses, e.g. `SSH` or `HTTP`, which expands to a set of protocol and port matches.",
    )
    log: PropertyRef = PropertyRef(
        "log",
        description="Log level for packets this rule matches: `nolog`, or a syslog level from `emerg` through `debug`.",
    )
    # IPSet references extracted from source/dest (prefixed with +)
    source_ipsets: PropertyRef = PropertyRef(
        "source_ipsets",
        description="Names of the IP sets referenced with `+` in `source`. Null when the rule references none.",
    )
    dest_ipsets: PropertyRef = PropertyRef(
        "dest_ipsets",
        description="Names of the IP sets referenced with `+` in `dest`. Null when the rule references none.",
    )


@dataclass(frozen=True)
class ProxmoxFirewallRuleToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallRuleToClusterRel(CartographyRelSchema):
    """
    Firewall rules belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
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


# ProxmoxFirewallIPSet Node Schema


@dataclass(frozen=True)
class ProxmoxFirewallIPSetNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxFirewallIPSet node.

    Represents IP sets (address groups) used in firewall rules.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this IP set, combining the scope it is defined at with its name.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the IP set, referenced from firewall rules as `+name`.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    scope: PropertyRef = PropertyRef(
        "scope",
        description="Level the IP set is defined at: `cluster`, `node` or `vm`.",
    )
    scope_id: PropertyRef = PropertyRef(
        "scope_id",
        description="Id of the object owning the IP set at that scope. Null for cluster-level IP sets.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment stored on the IP set."
    )
    cidrs: PropertyRef = PropertyRef(
        "cidrs", description="Addresses and CIDR ranges that are members of the set."
    )


@dataclass(frozen=True)
class ProxmoxFirewallIPSetToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallIPSetToClusterRel(CartographyRelSchema):
    """
    IP sets belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
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


# MatchLink Schemas for Firewall Relationships
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
    Connects VM-scoped firewall rules to the VMs they apply to.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid_int"),  # Integer VMID
            "cluster_id": PropertyRef("cluster_id"),  # Scope to same cluster
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
    in_source: PropertyRef = PropertyRef(
        "in_source",
        description="True when the rule references this IP set in its source match.",
    )
    in_dest: PropertyRef = PropertyRef(
        "in_dest",
        description="True when the rule references this IP set in its destination match.",
    )


@dataclass(frozen=True)
class ProxmoxFirewallRuleToIPSetMatchLink(CartographyRelSchema):
    """
    Connects firewall rules to the IPSets they reference in source/dest fields.
    """

    target_node_label: str = "ProxmoxFirewallIPSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("ipset_name"),
            "cluster_id": PropertyRef("cluster_id"),
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
