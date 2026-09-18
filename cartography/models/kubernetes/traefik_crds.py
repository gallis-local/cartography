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
    """Links a cluster to one of the Traefik custom resources deployed on it."""

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
    """Links a namespace to a Traefik custom resource it contains."""

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
# Shared: -> KubernetesService
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class TraefikToServiceRel(CartographyRelSchema):
    """Links a Traefik route to a Kubernetes service it routes traffic to."""

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
    id: PropertyRef = PropertyRef("uid", description="UID of the Traefik IngressRoute.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the Traefik IngressRoute.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this IngressRoute is deployed.",
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The `namespace/name` of the IngressRoute, unique within a cluster.",
    )
    entry_points: PropertyRef = PropertyRef(
        "entry_points",
        description="Names of the Traefik entry points this IngressRoute listens on (e.g. `web`, `websecure`). An entry point maps to a port on the Traefik proxy.",
    )
    ingress_class_name: PropertyRef = PropertyRef(
        "ingress_class_name",
        extra_index=True,
        description="The IngressClass this IngressRoute is bound to. Selects which Traefik instance serves the route when several are installed.",
    )
    hostnames: PropertyRef = PropertyRef(
        "hostnames",
        description="Hostnames named by the `Host()` predicates of the route match rules. Empty when the route matches on path or headers only.",
    )
    match_rules: PropertyRef = PropertyRef(
        "match_rules",
        description="The raw Traefik match rules of the route, one per route entry (e.g. ``Host(`a.example.com`) && PathPrefix(`/api`)``). Retains the path and header predicates that `hostnames` does not capture.",
    )
    traefik_service_names: PropertyRef = PropertyRef(
        "traefik_service_names",
        description="Backend references that point at a TraefikService rather than a Kubernetes Service (e.g. `api@internal`, or a weighted/mirroring TraefikService). These have no `TARGETS` relationship because they are not Kubernetes objects.",
    )
    has_tls: PropertyRef = PropertyRef(
        "has_tls",
        description="Whether the IngressRoute terminates TLS. True whenever a `tls` block is present, including an empty one, which terminates TLS using Traefik's default certificate.",
    )
    tls_secret_name: PropertyRef = PropertyRef(
        "tls_secret_name",
        description="Name of the Kubernetes secret holding the TLS certificate for this route.",
    )
    tls_cert_resolver: PropertyRef = PropertyRef(
        "tls_cert_resolver",
        description="Name of the Traefik certificate resolver that issues this route's certificate (e.g. an ACME resolver).",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Traefik IngressRoute.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this IngressRoute is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TraefikIngressRouteToMiddlewareRel(CartographyRelSchema):
    """Links a Traefik route to a middleware applied to its requests, whether attached to the router or to one of its backends."""

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
    """Links a Traefik IngressRoute to a parent IngressRoute whose routers it nests under, as configured by Traefik multi-layer routing."""

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
    "A Traefik IngressRoute custom resource that routes external HTTP traffic to Kubernetes services."

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
    id: PropertyRef = PropertyRef(
        "uid", description="UID of the Traefik IngressRouteTCP."
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the Traefik IngressRouteTCP.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this IngressRouteTCP is deployed.",
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The `namespace/name` of the IngressRouteTCP, unique within a cluster.",
    )
    entry_points: PropertyRef = PropertyRef(
        "entry_points",
        description="Names of the Traefik entry points this IngressRouteTCP listens on. An entry point maps to a port on the Traefik proxy.",
    )
    ingress_class_name: PropertyRef = PropertyRef(
        "ingress_class_name",
        extra_index=True,
        description="The IngressClass this IngressRouteTCP is bound to. Selects which Traefik instance serves the route when several are installed.",
    )
    hostnames: PropertyRef = PropertyRef(
        "hostnames",
        description="Hostnames named by the `HostSNI()` predicates of the route match rules. Empty when the route only matches the ``HostSNI(`*`)`` wildcard, which accepts any SNI.",
    )
    match_rules: PropertyRef = PropertyRef(
        "match_rules",
        description="The raw Traefik match rules of the route, one per route entry (e.g. ``HostSNI(`mqtt.example.com`)``).",
    )
    traefik_service_names: PropertyRef = PropertyRef(
        "traefik_service_names",
        description="Backend references that point at a TraefikService rather than a Kubernetes Service. These have no `TARGETS` relationship because they are not Kubernetes objects.",
    )
    has_tls: PropertyRef = PropertyRef(
        "has_tls",
        description="Whether the IngressRouteTCP has a TLS configuration. True whenever a `tls` block is present, including an empty one.",
    )
    tls_passthrough: PropertyRef = PropertyRef(
        "tls_passthrough",
        description="Whether Traefik forwards the TLS connection to the backend without terminating it. Null when the route has no TLS configuration at all.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Traefik IngressRouteTCP.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this IngressRouteTCP is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TraefikIngressRouteTCPSchema(CartographyNodeSchema):
    "A Traefik IngressRouteTCP custom resource that routes external TCP traffic to Kubernetes services."

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
    id: PropertyRef = PropertyRef(
        "uid", description="UID of the Traefik IngressRouteUDP."
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the Traefik IngressRouteUDP.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this IngressRouteUDP is deployed.",
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The `namespace/name` of the IngressRouteUDP, unique within a cluster.",
    )
    entry_points: PropertyRef = PropertyRef(
        "entry_points",
        description="Names of the Traefik entry points this IngressRouteUDP listens on. An entry point maps to a port on the Traefik proxy.",
    )
    ingress_class_name: PropertyRef = PropertyRef(
        "ingress_class_name",
        extra_index=True,
        description="The IngressClass this IngressRouteUDP is bound to. Selects which Traefik instance serves the route when several are installed.",
    )
    traefik_service_names: PropertyRef = PropertyRef(
        "traefik_service_names",
        description="Backend references that point at a TraefikService rather than a Kubernetes Service. These have no `TARGETS` relationship because they are not Kubernetes objects.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Traefik IngressRouteUDP.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this IngressRouteUDP is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TraefikIngressRouteUDPSchema(CartographyNodeSchema):
    "A Traefik IngressRouteUDP custom resource that routes external UDP traffic to Kubernetes services."

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
    id: PropertyRef = PropertyRef("uid", description="UID of the Traefik Middleware.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the Traefik Middleware.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this Middleware is deployed.",
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The `namespace/name` of the Middleware, unique within a cluster.",
    )
    middleware_type: PropertyRef = PropertyRef(
        "middleware_type",
        extra_index=True,
        description="The kind of middleware this resource configures, taken from the single key of its spec (e.g. `forwardAuth`, `ipAllowList`, `redirectScheme`, or `plugin` for a third-party plugin such as an OIDC authenticator). Null when the spec declares nothing usable.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Traefik Middleware.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this Middleware is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TraefikMiddlewareSchema(CartographyNodeSchema):
    "A Traefik Middleware custom resource that transforms or filters requests on their way to a backend, for example by enforcing authentication or an IP allow list."

    label: str = "TraefikMiddleware"
    properties: TraefikMiddlewareNodeProperties = TraefikMiddlewareNodeProperties()
    sub_resource_relationship: TraefikToClusterRel = TraefikToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TraefikToNamespaceRel(),
        ]
    )
