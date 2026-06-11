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


@dataclass(frozen=True)
class TraefikRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# ─────────────────────────────────────────────
# Shared sub-resource: -> KubernetesCluster
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class TraefikToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TraefikRelProperties = TraefikRelProperties()


# ─────────────────────────────────────────────
# Shared: -> KubernetesNamespace
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class TraefikToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: TraefikRelProperties = TraefikRelProperties()


# ─────────────────────────────────────────────
# Shared: -> KubernetesService (one_to_many)
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class TraefikToServiceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "qualified_name": PropertyRef(
                "backend_service_qualified_names",
                one_to_many=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: TraefikRelProperties = TraefikRelProperties()


# ═══════════════════════════════════════════════
# TraefikIngressRoute
# ═══════════════════════════════════════════════


@dataclass(frozen=True)
class TraefikIngressRouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    qualified_name: PropertyRef = PropertyRef("qualified_name", extra_index=True)
    entry_points: PropertyRef = PropertyRef("entry_points")
    hostnames: PropertyRef = PropertyRef("hostnames")
    has_tls: PropertyRef = PropertyRef("has_tls")
    tls_secret_name: PropertyRef = PropertyRef("tls_secret_name")
    tls_cert_resolver: PropertyRef = PropertyRef("tls_cert_resolver")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TraefikIngressRouteToMiddlewareRel(CartographyRelSchema):
    target_node_label: str = "TraefikMiddleware"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "qualified_name": PropertyRef(
                "middleware_qualified_names",
                one_to_many=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_MIDDLEWARE"
    properties: TraefikRelProperties = TraefikRelProperties()


@dataclass(frozen=True)
class TraefikIngressRouteToParentRel(CartographyRelSchema):
    target_node_label: str = "TraefikIngressRoute"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "qualified_name": PropertyRef(
                "parent_qualified_names",
                one_to_many=True,
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CHILD_OF"
    properties: TraefikRelProperties = TraefikRelProperties()


@dataclass(frozen=True)
class TraefikIngressRouteSchema(CartographyNodeSchema):
    label: str = "TraefikIngressRoute"
    properties: TraefikIngressRouteNodeProperties = TraefikIngressRouteNodeProperties()
    sub_resource_relationship: TraefikToClusterRel = TraefikToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TraefikToNamespaceRel(),
            TraefikToServiceRel(),
            TraefikIngressRouteToMiddlewareRel(),
            TraefikIngressRouteToParentRel(),
        ]
    )


# ═══════════════════════════════════════════════
# TraefikIngressRouteTCP
# ═══════════════════════════════════════════════


@dataclass(frozen=True)
class TraefikIngressRouteTCPNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    qualified_name: PropertyRef = PropertyRef("qualified_name", extra_index=True)
    entry_points: PropertyRef = PropertyRef("entry_points")
    has_tls: PropertyRef = PropertyRef("has_tls")
    tls_passthrough: PropertyRef = PropertyRef("tls_passthrough")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TraefikIngressRouteTCPSchema(CartographyNodeSchema):
    label: str = "TraefikIngressRouteTCP"
    properties: TraefikIngressRouteTCPNodeProperties = (
        TraefikIngressRouteTCPNodeProperties()
    )
    sub_resource_relationship: TraefikToClusterRel = TraefikToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TraefikToNamespaceRel(),
            TraefikToServiceRel(),
        ]
    )


# ═══════════════════════════════════════════════
# TraefikIngressRouteUDP
# ═══════════════════════════════════════════════


@dataclass(frozen=True)
class TraefikIngressRouteUDPNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    qualified_name: PropertyRef = PropertyRef("qualified_name", extra_index=True)
    entry_points: PropertyRef = PropertyRef("entry_points")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TraefikIngressRouteUDPSchema(CartographyNodeSchema):
    label: str = "TraefikIngressRouteUDP"
    properties: TraefikIngressRouteUDPNodeProperties = (
        TraefikIngressRouteUDPNodeProperties()
    )
    sub_resource_relationship: TraefikToClusterRel = TraefikToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TraefikToNamespaceRel(),
            TraefikToServiceRel(),
        ]
    )


# ═══════════════════════════════════════════════
# TraefikMiddleware
# ═══════════════════════════════════════════════


@dataclass(frozen=True)
class TraefikMiddlewareNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    qualified_name: PropertyRef = PropertyRef("qualified_name", extra_index=True)
    middleware_type: PropertyRef = PropertyRef("middleware_type", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TraefikMiddlewareSchema(CartographyNodeSchema):
    label: str = "TraefikMiddleware"
    properties: TraefikMiddlewareNodeProperties = TraefikMiddlewareNodeProperties()
    sub_resource_relationship: TraefikToClusterRel = TraefikToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TraefikToNamespaceRel(),
        ]
    )
