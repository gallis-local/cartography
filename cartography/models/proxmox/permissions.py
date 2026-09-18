"""
Derived permission relationships for Proxmox.

Proxmox expresses authorization as ACL entries: a path, a role and a principal
(user or group). Answering "what can this principal reach?" from that shape means
traversing ``principal <- ACL -> resource`` and ``ACL -> role`` on every query, so
these MatchLinks materialize the answer as a direct edge.

They are derived data, but they are still loaded through MatchLinks rather than a
hand-written MERGE so that ``GraphJob.from_matchlink`` owns the stale-edge cleanup
and scopes it to one cluster. A Proxmox install can hold several clusters, and a
cleanup that is not cluster-scoped either deletes another cluster's edges or keeps
refreshing them so they never expire.

A principal can reach the same resource through more than one ACL (two roles on the
same path, or directly plus via a group). Neo4j cannot hold two edges of the same
type between the same pair without duplicating them, so the contributing roles,
ACLs, privileges and paths are aggregated into list properties on the single edge.
Overwriting them with whichever ACL happened to be processed last would silently
drop real grants.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ProxmoxPermissionRelProperties(CartographyRelProperties):
    """
    Properties shared by every derived HAS_PERMISSION edge.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Aggregated across every ACL that contributes this grant.
    roles: PropertyRef = PropertyRef(
        "roles",
        description="Names of every role contributing this grant. A list because one principal can reach the same resource through several ACLs while only one edge can exist between the pair.",
    )
    privileges: PropertyRef = PropertyRef(
        "privileges",
        description="Union of the privileges granted by the contributing roles, e.g. `VM.Audit` or `VM.PowerMgmt`.",
    )
    via_acls: PropertyRef = PropertyRef(
        "via_acls",
        description="Ids of the `ProxmoxACL` entries that contribute this grant.",
    )
    paths: PropertyRef = PropertyRef(
        "paths",
        description="ACL paths the contributing entries are set on, e.g. `/` or `/vms/100`.",
    )
    # True if any contributing ACL propagates to child paths.
    propagate: PropertyRef = PropertyRef(
        "propagate",
        description="True when any contributing ACL propagates to child paths.",
    )
    # True if the grant reaches the principal through group membership.
    via_group: PropertyRef = PropertyRef(
        "via_group",
        description="True when the grant reaches the principal through group membership rather than an ACL on the principal itself.",
    )


# Target matchers, kept identical to the ProxmoxACLTo*MatchLink matchers in
# cartography.models.proxmox.access so a permission edge always lands on the same
# node the ACL edge landed on.

_VM_MATCHER = make_target_node_matcher(
    {
        "vmid": PropertyRef("resource_id_int"),
        "cluster_id": PropertyRef("cluster_id"),
    }
)
_STORAGE_MATCHER = make_target_node_matcher(
    {
        "name": PropertyRef("resource_id"),
        "cluster_id": PropertyRef("cluster_id"),
    }
)
_POOL_MATCHER = make_target_node_matcher(
    {
        "poolid": PropertyRef("resource_id"),
        "cluster_id": PropertyRef("cluster_id"),
    }
)
_NODE_MATCHER = make_target_node_matcher(
    {
        "name": PropertyRef("resource_id"),
        "cluster_id": PropertyRef("cluster_id"),
    }
)
_CLUSTER_MATCHER = make_target_node_matcher(
    {
        "id": PropertyRef("cluster_id"),
    }
)

_PRINCIPAL_MATCHER = make_source_node_matcher({"id": PropertyRef("principal_id")})


# --- User -> resource ---------------------------------------------------------


@dataclass(frozen=True)
class ProxmoxUserToVMPermissionMatchLink(CartographyRelSchema):
    """Effective permission from a user to a VM."""

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = _VM_MATCHER
    source_node_label: str = "ProxmoxUser"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


@dataclass(frozen=True)
class ProxmoxUserToStoragePermissionMatchLink(CartographyRelSchema):
    """Effective permission from a user to a storage backend."""

    target_node_label: str = "ProxmoxStorage"
    target_node_matcher: TargetNodeMatcher = _STORAGE_MATCHER
    source_node_label: str = "ProxmoxUser"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


@dataclass(frozen=True)
class ProxmoxUserToPoolPermissionMatchLink(CartographyRelSchema):
    """Effective permission from a user to a resource pool."""

    target_node_label: str = "ProxmoxPool"
    target_node_matcher: TargetNodeMatcher = _POOL_MATCHER
    source_node_label: str = "ProxmoxUser"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


@dataclass(frozen=True)
class ProxmoxUserToNodePermissionMatchLink(CartographyRelSchema):
    """Effective permission from a user to a cluster node."""

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = _NODE_MATCHER
    source_node_label: str = "ProxmoxUser"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


@dataclass(frozen=True)
class ProxmoxUserToClusterPermissionMatchLink(CartographyRelSchema):
    """Effective permission from a user to the cluster itself (root path grants)."""

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = _CLUSTER_MATCHER
    source_node_label: str = "ProxmoxUser"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


# --- Group -> resource --------------------------------------------------------


@dataclass(frozen=True)
class ProxmoxGroupToVMPermissionMatchLink(CartographyRelSchema):
    """Effective permission from a group to a VM."""

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = _VM_MATCHER
    source_node_label: str = "ProxmoxGroup"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


@dataclass(frozen=True)
class ProxmoxGroupToStoragePermissionMatchLink(CartographyRelSchema):
    """Effective permission from a group to a storage backend."""

    target_node_label: str = "ProxmoxStorage"
    target_node_matcher: TargetNodeMatcher = _STORAGE_MATCHER
    source_node_label: str = "ProxmoxGroup"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


@dataclass(frozen=True)
class ProxmoxGroupToPoolPermissionMatchLink(CartographyRelSchema):
    """Effective permission from a group to a resource pool."""

    target_node_label: str = "ProxmoxPool"
    target_node_matcher: TargetNodeMatcher = _POOL_MATCHER
    source_node_label: str = "ProxmoxGroup"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


@dataclass(frozen=True)
class ProxmoxGroupToNodePermissionMatchLink(CartographyRelSchema):
    """Effective permission from a group to a cluster node."""

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = _NODE_MATCHER
    source_node_label: str = "ProxmoxGroup"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


@dataclass(frozen=True)
class ProxmoxGroupToClusterPermissionMatchLink(CartographyRelSchema):
    """Effective permission from a group to the cluster itself (root path grants)."""

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = _CLUSTER_MATCHER
    source_node_label: str = "ProxmoxGroup"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: ProxmoxPermissionRelProperties = ProxmoxPermissionRelProperties()


# --- User -> role -------------------------------------------------------------


@dataclass(frozen=True)
class ProxmoxUserToRoleRelProperties(CartographyRelProperties):
    """
    Properties for the derived user-to-role edge.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # A user can hold the same role on several paths; keep all of them.
    paths: PropertyRef = PropertyRef(
        "paths",
        description="ACL paths on which the user holds this role. A list because the same role can be granted on several paths.",
    )
    propagate: PropertyRef = PropertyRef(
        "propagate",
        description="True when any contributing ACL propagates to child paths.",
    )
    via_group: PropertyRef = PropertyRef(
        "via_group",
        description="True when the role reaches the user through group membership rather than an ACL on the user itself.",
    )


@dataclass(frozen=True)
class ProxmoxUserToRoleMatchLink(CartographyRelSchema):
    """
    A role held by a user.

    Proxmox only relates the two through an intervening ACL entry, so this edge
    states the role assignment directly.
    """

    target_node_label: str = "ProxmoxRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "roleid": PropertyRef("roleid"),
            "cluster_id": PropertyRef("cluster_id"),
        }
    )
    source_node_label: str = "ProxmoxUser"
    source_node_matcher: SourceNodeMatcher = _PRINCIPAL_MATCHER
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: ProxmoxUserToRoleRelProperties = ProxmoxUserToRoleRelProperties()
