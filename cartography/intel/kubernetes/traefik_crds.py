import logging
import re
from collections.abc import Iterator
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import get_qualified_resource_name
from cartography.intel.kubernetes.util import K8sClient
from cartography.intel.kubernetes.util import parse_rfc3339
from cartography.models.kubernetes.traefik_crds import TraefikIngressRouteSchema
from cartography.models.kubernetes.traefik_crds import TraefikIngressRouteTCPSchema
from cartography.models.kubernetes.traefik_crds import TraefikIngressRouteUDPSchema
from cartography.models.kubernetes.traefik_crds import TraefikMiddlewareSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

TRAEFIK_API_GROUP = "traefik.io"
TRAEFIK_API_VERSION = "v1alpha1"

# Known HTTP middleware types (keys that may appear as subfields of spec). Kept as a
# sorted tuple rather than a set so that a spec declaring more than one type always
# yields the same middleware_type instead of varying with hash ordering.
MIDDLEWARE_TYPE_KEYS: tuple[str, ...] = tuple(
    sorted(
        (
            "addPrefix",
            "basicAuth",
            "buffering",
            "chain",
            "circuitBreaker",
            "compress",
            "contentType",
            "digestAuth",
            "errors",
            "forwardAuth",
            "grpcWeb",
            "headers",
            "plugin",
            "ipAllowList",
            "ipWhiteList",
            "inFlightReq",
            "passTLSClientCert",
            "rateLimit",
            "redirectRegex",
            "redirectScheme",
            "replacePath",
            "replacePathRegex",
            "retry",
            "stripPrefix",
            "stripPrefixRegex",
        )
    )
)

# Traefik route match rules name hosts with Host(`a`) / HostSNI(`a`), and a single call
# may carry several comma-separated arguments, so the call body is captured whole and
# the individual backtick-quoted hosts are pulled out of it afterwards.
_HOST_CALL_RE = re.compile(r"\bHost(?:SNI)?\(([^)]*)\)")
_QUOTED_RE = re.compile(r"`([^`]+)`")


def _list_cluster_custom_objects(
    client: K8sClient,
    group: str,
    version: str,
    plural: str,
) -> list[dict[str, Any]] | None:
    """List every object of a Traefik CRD, following pagination.

    :param client: The Kubernetes client for the cluster being synced.
    :param group: API group of the custom resource.
    :param version: API version of the custom resource.
    :param plural: Plural resource name of the custom resource.
    :return: The objects found, or ``None`` when the CRD is not installed. The two are
        deliberately distinct: an empty list means Traefik is installed and currently
        has no objects of this kind, which must still trigger cleanup of previously
        synced nodes, whereas ``None`` means there is nothing to sync at all.
    """
    resource_name = f"{group}/{version}/{plural}"
    all_resources: list[dict[str, Any]] = []
    continue_token: str | None = None

    while True:
        kwargs: dict[str, Any] = {}
        if continue_token:
            kwargs["_continue"] = continue_token

        try:
            response = client.custom.list_cluster_custom_object(
                group=group,
                version=version,
                plural=plural,
                limit=100,
                **kwargs,
            )
        except ApiException as err:
            if err.status == 404:
                logger.info(
                    "Skipping %s for cluster %s because the CRD is not installed.",
                    resource_name,
                    client.name,
                )
                return None

            logger.warning(
                "Failed to fetch %s resources for cluster %s: %s",
                resource_name,
                client.name,
                err,
            )
            raise

        items = response.get("items", [])
        all_resources.extend(items)

        continue_token = response.get("metadata", {}).get("continue")
        if not continue_token:
            break

    logger.debug("Fetched %d %s resources", len(all_resources), resource_name)
    return all_resources


# ─────────────────────────────────────────────────────
# GET functions
# ─────────────────────────────────────────────────────


@timeit
def get_ingressroutes(client: K8sClient) -> list[dict[str, Any]] | None:
    return _list_cluster_custom_objects(
        client,
        TRAEFIK_API_GROUP,
        TRAEFIK_API_VERSION,
        "ingressroutes",
    )


@timeit
def get_ingressroutetcps(client: K8sClient) -> list[dict[str, Any]] | None:
    return _list_cluster_custom_objects(
        client,
        TRAEFIK_API_GROUP,
        TRAEFIK_API_VERSION,
        "ingressroutetcps",
    )


@timeit
def get_ingressrouteudps(client: K8sClient) -> list[dict[str, Any]] | None:
    return _list_cluster_custom_objects(
        client,
        TRAEFIK_API_GROUP,
        TRAEFIK_API_VERSION,
        "ingressrouteudps",
    )


@timeit
def get_middlewares(client: K8sClient) -> list[dict[str, Any]] | None:
    return _list_cluster_custom_objects(
        client,
        TRAEFIK_API_GROUP,
        TRAEFIK_API_VERSION,
        "middlewares",
    )


# ─────────────────────────────────────────────────────
# Transform helpers
# ─────────────────────────────────────────────────────


def _extract_hostnames(match: str) -> list[str]:
    """Pull the hostnames out of a Traefik route match rule.

    :param match: A raw Traefik match rule, e.g. ``Host(`a.example.com`) && PathPrefix(`/x`)``.
    :return: The hostnames named by ``Host``/``HostSNI``, in rule order and de-duplicated.
        The ``HostSNI(`*`)`` wildcard is dropped because it matches any SNI (or none at
        all) rather than naming a host, so treating it as a hostname would make
        hostname-based exposure queries return a literal asterisk.
    """
    hostnames: list[str] = []
    for call_body in _HOST_CALL_RE.findall(match or ""):
        for host in _QUOTED_RE.findall(call_body):
            if host != "*" and host not in hostnames:
                hostnames.append(host)
    return hostnames


def _extract_match_rules(routes: list[dict[str, Any]]) -> list[str]:
    """Collect the raw match rules of a route set so path/header predicates stay queryable.

    :param routes: The ``spec.routes`` entries of an IngressRoute or IngressRouteTCP.
    :return: The non-empty ``match`` strings, in spec order.
    """
    return [route["match"] for route in routes if route.get("match")]


def _get_middleware_type(spec: dict[str, Any]) -> str | None:
    """Determine which middleware a Traefik Middleware spec configures.

    A Middleware spec names its type with a single key, so an unrecognised key is still
    reported rather than discarded: Traefik adds middleware types (and ``plugin``
    middlewares wrap arbitrary third-party auth), and silently collapsing those to a
    sentinel would hide authentication middleware from security queries.

    :param spec: The ``spec`` of a Traefik Middleware object.
    :return: The middleware type, or None if the spec declares nothing usable.
    """
    known = [key for key in MIDDLEWARE_TYPE_KEYS if key in spec]
    if known:
        return known[0]
    keys = sorted(spec.keys())
    return keys[0] if len(keys) == 1 else None


def _iter_service_refs(routes: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for route in routes:
        yield from route.get("services") or []


def _collect_service_qualified_names(
    routes: list[dict[str, Any]],
    default_namespace: str,
) -> list[str]:
    """Collect the Kubernetes Services a route set sends traffic to.

    :param routes: The ``spec.routes`` entries of a route object.
    :param default_namespace: Namespace of the route object, used when a backend
        reference omits one.
    :return: Sorted ``namespace/name`` keys of the referenced Kubernetes Services.
    """
    seen: set[str] = set()
    for svc in _iter_service_refs(routes):
        # kind defaults to Service; a TraefikService backend (e.g. api@internal or a
        # weighted/mirroring TraefikService) is not a Kubernetes Service, so emitting it
        # here would produce a qualified name that can never match any node.
        if (svc.get("kind") or "Service") != "Service":
            continue
        ns = svc.get("namespace") or default_namespace
        name = svc.get("name")
        if name and ns:
            seen.add(get_qualified_resource_name(ns, name))
    return sorted(seen)


def _collect_traefik_service_names(routes: list[dict[str, Any]]) -> list[str]:
    """Collect backend references that point at TraefikServices rather than Services.

    Recording these keeps a route whose only backend is a TraefikService distinguishable
    from a route whose Kubernetes Service backend failed to resolve.

    :param routes: The ``spec.routes`` entries of a route object.
    :return: Sorted names of the referenced TraefikServices.
    """
    seen: set[str] = set()
    for svc in _iter_service_refs(routes):
        if (svc.get("kind") or "Service") == "Service":
            continue
        name = svc.get("name")
        if name:
            seen.add(name)
    return sorted(seen)


def _collect_middleware_qualified_names(
    routes: list[dict[str, Any]],
    default_namespace: str,
) -> list[str]:
    """Collect the Middlewares a route set applies.

    :param routes: The ``spec.routes`` entries of a route object.
    :param default_namespace: Namespace of the route object, used when a middleware
        reference omits one.
    :return: Sorted ``namespace/name`` keys of the referenced Middlewares.
    """
    seen: set[str] = set()
    # Middlewares attach at two levels: to the router (route.middlewares) and to an
    # individual backend (route.services[].middlewares). Both sit on the request path, so
    # ignoring the second level under-reports the auth applied to a route.
    refs: list[dict[str, Any]] = []
    for route in routes:
        refs.extend(route.get("middlewares") or [])
        for svc in route.get("services") or []:
            refs.extend(svc.get("middlewares") or [])

    for mw in refs:
        name = mw.get("name")
        if not name:
            continue
        ns = mw.get("namespace") or default_namespace
        if "@" in name:
            # Traefik also accepts a fully qualified provider name such as
            # "stripprefix@kubernetescrd". The suffix is not part of the Kubernetes object
            # name, and the "namespace-name@kubernetescrd" variant cannot be split back
            # into namespace and name unambiguously, so warn instead of guessing silently.
            logger.warning(
                "Middleware reference %r uses Traefik's provider-qualified syntax; "
                "resolving it against namespace %s, which is wrong if the middleware "
                "lives in another namespace.",
                name,
                ns,
            )
            name = name.split("@", 1)[0]
        seen.add(get_qualified_resource_name(ns, name))
    return sorted(seen)


def _collect_parent_qualified_names(
    spec: dict[str, Any],
    default_namespace: str,
) -> list[str]:
    seen: set[str] = set()
    for parent_ref in spec.get("parentRefs") or []:
        ns = parent_ref.get("namespace") or default_namespace
        name = parent_ref.get("name")
        if name and ns:
            seen.add(get_qualified_resource_name(ns, name))
    return sorted(seen)


# ─────────────────────────────────────────────────────
# TRANSFORM functions
# ─────────────────────────────────────────────────────


def transform_ingressroutes(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for item in items:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        namespace = metadata["namespace"]
        name = metadata["name"]

        entry_points = spec.get("entryPoints") or []
        routes = spec.get("routes") or []

        hostnames: list[str] = []
        for route in routes:
            for hostname in _extract_hostnames(route.get("match", "")):
                if hostname not in hostnames:
                    hostnames.append(hostname)

        # `tls: {}` is a valid spec that terminates TLS with Traefik's default
        # certificate, so TLS termination is keyed on the field being present rather than
        # on it being non-empty -- otherwise such a route reads as plaintext.
        tls = spec.get("tls")
        has_tls = tls is not None
        tls = tls or {}

        transformed.append(
            {
                "uid": metadata["uid"],
                "name": name,
                "namespace": namespace,
                "qualified_name": get_qualified_resource_name(namespace, name),
                "entry_points": entry_points,
                "ingress_class_name": spec.get("ingressClassName"),
                "hostnames": hostnames,
                "match_rules": _extract_match_rules(routes),
                "has_tls": has_tls,
                "tls_secret_name": tls.get("secretName"),
                "tls_cert_resolver": tls.get("certResolver"),
                "backend_service_qualified_names": (
                    _collect_service_qualified_names(routes, namespace)
                ),
                "traefik_service_names": _collect_traefik_service_names(routes),
                "middleware_qualified_names": (
                    _collect_middleware_qualified_names(routes, namespace)
                ),
                "parent_qualified_names": (
                    _collect_parent_qualified_names(spec, namespace)
                ),
                "creation_timestamp": get_epoch(
                    parse_rfc3339(metadata.get("creationTimestamp")),
                ),
            }
        )
    return transformed


def transform_ingressroutetcps(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for item in items:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        namespace = metadata["namespace"]
        name = metadata["name"]

        entry_points = spec.get("entryPoints") or []
        routes = spec.get("routes") or []

        # TCP routes name their host with HostSNI(), and that SNI is the only
        # hostname-shaped handle on the route, so it is extracted exactly as for HTTP.
        hostnames: list[str] = []
        for route in routes:
            for hostname in _extract_hostnames(route.get("match", "")):
                if hostname not in hostnames:
                    hostnames.append(hostname)

        tls = spec.get("tls")
        has_tls = tls is not None
        transformed.append(
            {
                "uid": metadata["uid"],
                "name": name,
                "namespace": namespace,
                "qualified_name": get_qualified_resource_name(namespace, name),
                "entry_points": entry_points,
                "ingress_class_name": spec.get("ingressClassName"),
                "hostnames": hostnames,
                "match_rules": _extract_match_rules(routes),
                "has_tls": has_tls,
                # Left None rather than False when the route has no TLS block at all, so
                # "TLS terminated by Traefik" stays distinguishable from "no TLS".
                "tls_passthrough": (
                    (tls or {}).get("passthrough", False) if has_tls else None
                ),
                "backend_service_qualified_names": (
                    _collect_service_qualified_names(routes, namespace)
                ),
                "traefik_service_names": _collect_traefik_service_names(routes),
                "creation_timestamp": get_epoch(
                    parse_rfc3339(metadata.get("creationTimestamp")),
                ),
            }
        )
    return transformed


def transform_ingressrouteudps(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for item in items:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        namespace = metadata["namespace"]
        name = metadata["name"]

        entry_points = spec.get("entryPoints") or []
        routes = spec.get("routes") or []

        transformed.append(
            {
                "uid": metadata["uid"],
                "name": name,
                "namespace": namespace,
                "qualified_name": get_qualified_resource_name(namespace, name),
                "entry_points": entry_points,
                "ingress_class_name": spec.get("ingressClassName"),
                "backend_service_qualified_names": (
                    _collect_service_qualified_names(routes, namespace)
                ),
                "traefik_service_names": _collect_traefik_service_names(routes),
                "creation_timestamp": get_epoch(
                    parse_rfc3339(metadata.get("creationTimestamp")),
                ),
            }
        )
    return transformed


def transform_middlewares(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for item in items:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        namespace = metadata["namespace"]
        name = metadata["name"]

        middleware_type = _get_middleware_type(spec)

        transformed.append(
            {
                "uid": metadata["uid"],
                "name": name,
                "namespace": namespace,
                "qualified_name": get_qualified_resource_name(namespace, name),
                "middleware_type": middleware_type,
                "creation_timestamp": get_epoch(
                    parse_rfc3339(metadata.get("creationTimestamp")),
                ),
            }
        )
    return transformed


# ─────────────────────────────────────────────────────
# LOAD functions
# ─────────────────────────────────────────────────────


@timeit
def load_ingressroutes(
    neo4j_session: neo4j.Session,
    items: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        neo4j_session,
        TraefikIngressRouteSchema(),
        items,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def load_ingressroutetcps(
    neo4j_session: neo4j.Session,
    items: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        neo4j_session,
        TraefikIngressRouteTCPSchema(),
        items,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def load_ingressrouteudps(
    neo4j_session: neo4j.Session,
    items: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        neo4j_session,
        TraefikIngressRouteUDPSchema(),
        items,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def load_middlewares(
    neo4j_session: neo4j.Session,
    items: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        neo4j_session,
        TraefikMiddlewareSchema(),
        items,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


# ─────────────────────────────────────────────────────
# CLEANUP
# ─────────────────────────────────────────────────────


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running cleanup job for Traefik CRD resources")
    GraphJob.from_node_schema(
        TraefikIngressRouteSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        TraefikIngressRouteTCPSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        TraefikIngressRouteUDPSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        TraefikMiddlewareSchema(),
        common_job_parameters,
    ).run(neo4j_session)


# ─────────────────────────────────────────────────────
# SYNC orchestrator
# ─────────────────────────────────────────────────────


@timeit
def sync_traefik_crds(
    neo4j_session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    cluster_id = common_job_parameters.get("CLUSTER_ID")
    if not cluster_id:
        logger.warning(
            "No CLUSTER_ID in common_job_parameters — skipping Traefik CRD sync.",
        )
        return

    try:
        raw_ingressroutes = get_ingressroutes(client)
        raw_ingressroutetcps = get_ingressroutetcps(client)
        raw_ingressrouteudps = get_ingressrouteudps(client)
        raw_middlewares = get_middlewares(client)
    except ApiException as err:
        if err.status in (401, 403):
            logger.warning(
                "Cartography lacks permission to list Traefik CRDs on "
                "cluster %s (status %s). Skipping Traefik sync and "
                "preserving previously synced data.",
                client.name,
                err.status,
            )
            return
        raise

    fetched = (
        raw_ingressroutes,
        raw_ingressroutetcps,
        raw_ingressrouteudps,
        raw_middlewares,
    )
    if all(result is None for result in fetched):
        logger.debug("No Traefik CRDs installed on cluster %s — skipping.", client.name)
        return

    # From here on an empty result means "installed, but currently no objects", which must
    # still fall through to cleanup so that nodes for deleted routes are removed instead of
    # lingering in the graph forever.
    middlewares = transform_middlewares(raw_middlewares or [])
    ingressroutes = transform_ingressroutes(raw_ingressroutes or [])
    ingressroutetcps = transform_ingressroutetcps(raw_ingressroutetcps or [])
    ingressrouteudps = transform_ingressrouteudps(raw_ingressrouteudps or [])

    cluster_name = client.name

    # Load Middlewares first so IngressRoute->USES_MIDDLEWARE edges resolve
    load_middlewares(
        neo4j_session,
        middlewares,
        update_tag,
        cluster_id,
        cluster_name,
    )
    load_ingressroutes(
        neo4j_session,
        ingressroutes,
        update_tag,
        cluster_id,
        cluster_name,
    )
    load_ingressroutetcps(
        neo4j_session,
        ingressroutetcps,
        update_tag,
        cluster_id,
        cluster_name,
    )
    load_ingressrouteudps(
        neo4j_session,
        ingressrouteudps,
        update_tag,
        cluster_id,
        cluster_name,
    )

    cleanup(neo4j_session, common_job_parameters)

    logger.info(
        "Synced %d IngressRoutes, %d IngressRouteTCPs, %d IngressRouteUDPs, %d Middlewares "
        "for cluster %s",
        len(ingressroutes),
        len(ingressroutetcps),
        len(ingressrouteudps),
        len(middlewares),
        cluster_name,
    )
