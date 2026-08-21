"""
Data models for Proxmox access control (users, groups, roles, ACLs).

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import PERMISSION_ROLE
from cartography.models.ontology.labels import USER_ACCOUNT
from cartography.models.ontology.labels import USER_GROUP

# ProxmoxUser Node Schema


@dataclass(frozen=True)
class ProxmoxUserNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxUser node.

    Represents user accounts in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    userid: PropertyRef = PropertyRef("userid", extra_index=True)
    realm: PropertyRef = PropertyRef("realm", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    enable: PropertyRef = PropertyRef("enable")
    expire: PropertyRef = PropertyRef("expire")
    firstname: PropertyRef = PropertyRef("firstname")
    lastname: PropertyRef = PropertyRef("lastname")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    groups: PropertyRef = PropertyRef("groups")
    tokens: PropertyRef = PropertyRef("tokens")


@dataclass(frozen=True)
class ProxmoxUserToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxUserToClusterRel(CartographyRelSchema):
    """
    Users belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxUserToClusterRelProperties = ProxmoxUserToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxUserToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxUserToGroupRel(CartographyRelSchema):
    """
    Users are members of groups.
    """

    target_node_label: str = "ProxmoxGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "groupid": PropertyRef("groups", one_to_many=True),
            "cluster_id": PropertyRef("cluster_id"),  # Must match same cluster
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: ProxmoxUserToGroupRelProperties = ProxmoxUserToGroupRelProperties()


@dataclass(frozen=True)
class ProxmoxUserToAuthRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxUserToAuthRealmRel(CartographyRelSchema):
    """
    Users authenticate via a realm (PAM, LDAP, AD, OpenID, etc.).
    Enables queries like "find all users using LDAP" without string parsing.
    """

    target_node_label: str = "ProxmoxAuthRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "realm": PropertyRef("realm"),
            "cluster_id": PropertyRef("cluster_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AUTHENTICATES_VIA"
    properties: ProxmoxUserToAuthRealmRelProperties = (
        ProxmoxUserToAuthRealmRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxUserSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxUser.

    User accounts for Proxmox VE authentication and authorization.
    """

    label: str = "ProxmoxUser"
    properties: ProxmoxUserNodeProperties = ProxmoxUserNodeProperties()
    sub_resource_relationship: ProxmoxUserToClusterRel = ProxmoxUserToClusterRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxUserToGroupRel(),
            ProxmoxUserToAuthRealmRel(),
        ]
    )


# ProxmoxGroup Node Schema


@dataclass(frozen=True)
class ProxmoxGroupNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxGroup node.

    Represents user groups in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    groupid: PropertyRef = PropertyRef("groupid", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    comment: PropertyRef = PropertyRef("comment")


@dataclass(frozen=True)
class ProxmoxGroupToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxGroupToClusterRel(CartographyRelSchema):
    """
    Groups belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxGroupToClusterRelProperties = (
        ProxmoxGroupToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxGroupSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxGroup.

    User groups for organizing permissions in Proxmox VE.
    """

    label: str = "ProxmoxGroup"
    properties: ProxmoxGroupNodeProperties = ProxmoxGroupNodeProperties()
    sub_resource_relationship: ProxmoxGroupToClusterRel = ProxmoxGroupToClusterRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])


# ProxmoxRole Node Schema


@dataclass(frozen=True)
class ProxmoxRoleNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxRole node.

    Represents permission roles in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    roleid: PropertyRef = PropertyRef("roleid", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    privs: PropertyRef = PropertyRef("privs")
    special: PropertyRef = PropertyRef("special")


@dataclass(frozen=True)
class ProxmoxRoleToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxRoleToClusterRel(CartographyRelSchema):
    """
    Roles belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxRoleToClusterRelProperties = ProxmoxRoleToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxRoleSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxRole.

    Permission roles defining what actions users can perform.
    """

    label: str = "ProxmoxRole"
    properties: ProxmoxRoleNodeProperties = ProxmoxRoleNodeProperties()
    sub_resource_relationship: ProxmoxRoleToClusterRel = ProxmoxRoleToClusterRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])


# ProxmoxACL Node Schema


@dataclass(frozen=True)
class ProxmoxACLNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxACL node.

    Represents Access Control List entries granting permissions.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    path: PropertyRef = PropertyRef("path", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    roleid: PropertyRef = PropertyRef("roleid")
    ugid: PropertyRef = PropertyRef("ugid", extra_index=True)
    propagate: PropertyRef = PropertyRef("propagate")
    principal_type: PropertyRef = PropertyRef("principal_type")
    resource_type: PropertyRef = PropertyRef("resource_type")
    resource_id: PropertyRef = PropertyRef("resource_id")


@dataclass(frozen=True)
class ProxmoxACLToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxACLToClusterRel(CartographyRelSchema):
    """
    ACLs belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxACLToClusterRelProperties = ProxmoxACLToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxACLToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxACLToRoleRel(CartographyRelSchema):
    """
    ACLs grant roles to users/groups.
    Includes metadata about permission scope and propagation.
    """

    target_node_label: str = "ProxmoxRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "roleid": PropertyRef("roleid"),
            "cluster_id": PropertyRef("cluster_id"),  # Must match same cluster
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ROLE"
    properties: ProxmoxACLToRoleRelProperties = ProxmoxACLToRoleRelProperties()


@dataclass(frozen=True)
class ProxmoxACLToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    path: PropertyRef = PropertyRef("path")
    propagate: PropertyRef = PropertyRef("propagate")
    resource_type: PropertyRef = PropertyRef("resource_type")


@dataclass(frozen=True)
class ProxmoxACLToUserRel(CartographyRelSchema):
    """
    ACLs apply permissions to specific users.
    Includes metadata about permission scope, path, and propagation.
    """

    target_node_label: str = "ProxmoxUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "userid": PropertyRef("base_userid"),
            "cluster_id": PropertyRef("cluster_id"),  # Must match same cluster
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO_USER"
    properties: ProxmoxACLToUserRelProperties = ProxmoxACLToUserRelProperties()


@dataclass(frozen=True)
class ProxmoxACLToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    path: PropertyRef = PropertyRef("path")
    propagate: PropertyRef = PropertyRef("propagate")
    resource_type: PropertyRef = PropertyRef("resource_type")


@dataclass(frozen=True)
class ProxmoxACLToGroupRel(CartographyRelSchema):
    """
    ACLs apply permissions to groups.
    Includes metadata about permission scope, path, and propagation.
    """

    target_node_label: str = "ProxmoxGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "groupid": PropertyRef("ugid"),
            "cluster_id": PropertyRef("cluster_id"),  # Must match same cluster
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO_GROUP"
    properties: ProxmoxACLToGroupRelProperties = ProxmoxACLToGroupRelProperties()


@dataclass(frozen=True)
class ProxmoxACLSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxACL.

    Access Control List entries defining permissions.
    """

    label: str = "ProxmoxACL"
    properties: ProxmoxACLNodeProperties = ProxmoxACLNodeProperties()
    sub_resource_relationship: ProxmoxACLToClusterRel = ProxmoxACLToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxACLToRoleRel(),
            ProxmoxACLToUserRel(),
            ProxmoxACLToGroupRel(),
        ]
    )


# MatchLink Schemas for ACL Resource Permissions
# These MatchLinks connect ACLs to the resources they grant access to.
# We use MatchLinks here because:
# 1. ACLs can grant access to different types of resources (VMs, Storage, Pools, Nodes, Clusters)
# 2. The resource data comes from separate API calls/sync functions
# 3. We need rich relationship properties (path, propagate)


@dataclass(frozen=True)
class ProxmoxACLToVMMatchLinkProperties(CartographyRelProperties):
    """
    Properties for ACL to VM GRANTS_ACCESS_TO relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Relationship metadata
    propagate: PropertyRef = PropertyRef("propagate")
    path: PropertyRef = PropertyRef("path")


@dataclass(frozen=True)
class ProxmoxACLToVMMatchLink(CartographyRelSchema):
    """
    Connects ACLs to the VMs they grant permissions to.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("resource_id_int"),  # Integer VMID
            "cluster_id": PropertyRef("cluster_id"),  # Must match same cluster
        }
    )
    source_node_label: str = "ProxmoxACL"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ACCESS_TO"
    properties: ProxmoxACLToVMMatchLinkProperties = ProxmoxACLToVMMatchLinkProperties()


@dataclass(frozen=True)
class ProxmoxACLToStorageMatchLinkProperties(CartographyRelProperties):
    """
    Properties for ACL to Storage GRANTS_ACCESS_TO relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Relationship metadata
    propagate: PropertyRef = PropertyRef("propagate")
    path: PropertyRef = PropertyRef("path")


@dataclass(frozen=True)
class ProxmoxACLToStorageMatchLink(CartographyRelSchema):
    """
    Connects ACLs to the storage they grant permissions to.
    """

    target_node_label: str = "ProxmoxStorage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("resource_id"),  # Storage name
            "cluster_id": PropertyRef("cluster_id"),  # Must match same cluster
        }
    )
    source_node_label: str = "ProxmoxACL"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ACCESS_TO"
    properties: ProxmoxACLToStorageMatchLinkProperties = (
        ProxmoxACLToStorageMatchLinkProperties()
    )


@dataclass(frozen=True)
class ProxmoxACLToPoolMatchLinkProperties(CartographyRelProperties):
    """
    Properties for ACL to Pool GRANTS_ACCESS_TO relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Relationship metadata
    propagate: PropertyRef = PropertyRef("propagate")
    path: PropertyRef = PropertyRef("path")


@dataclass(frozen=True)
class ProxmoxACLToPoolMatchLink(CartographyRelSchema):
    """
    Connects ACLs to the pools they grant permissions to.
    """

    target_node_label: str = "ProxmoxPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "poolid": PropertyRef("resource_id"),  # Pool ID as string
            "cluster_id": PropertyRef("cluster_id"),  # Must match same cluster
        }
    )
    source_node_label: str = "ProxmoxACL"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ACCESS_TO"
    properties: ProxmoxACLToPoolMatchLinkProperties = (
        ProxmoxACLToPoolMatchLinkProperties()
    )


@dataclass(frozen=True)
class ProxmoxACLToNodeMatchLinkProperties(CartographyRelProperties):
    """
    Properties for ACL to Node GRANTS_ACCESS_TO relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Relationship metadata
    propagate: PropertyRef = PropertyRef("propagate")
    path: PropertyRef = PropertyRef("path")


@dataclass(frozen=True)
class ProxmoxACLToNodeMatchLink(CartographyRelSchema):
    """
    Connects ACLs to the nodes they grant permissions to.
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("resource_id"),  # Node name
            "cluster_id": PropertyRef("cluster_id"),  # Must match same cluster
        }
    )
    source_node_label: str = "ProxmoxACL"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ACCESS_TO"
    properties: ProxmoxACLToNodeMatchLinkProperties = (
        ProxmoxACLToNodeMatchLinkProperties()
    )


@dataclass(frozen=True)
class ProxmoxACLToClusterMatchLinkProperties(CartographyRelProperties):
    """
    Properties for ACL to Cluster GRANTS_ACCESS_TO relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Relationship metadata
    propagate: PropertyRef = PropertyRef("propagate")
    path: PropertyRef = PropertyRef("path")


@dataclass(frozen=True)
class ProxmoxACLToClusterMatchLink(CartographyRelSchema):
    """
    Connects ACLs to the cluster (root level permissions).
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("cluster_id"),  # Cluster ID
        }
    )
    source_node_label: str = "ProxmoxACL"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ACCESS_TO"
    properties: ProxmoxACLToClusterMatchLinkProperties = (
        ProxmoxACLToClusterMatchLinkProperties()
    )
