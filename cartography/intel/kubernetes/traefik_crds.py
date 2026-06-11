import logging
import re
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

# All known HTTP middleware types (keys that may appear as subfields of spec)
MIDDLEWARE_TYPE_KEYS = frozenset(
    {
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
    }
)

_HOSTNAME_RE = re.compile(r"Host(?:SNI)?\(`([^`]+)`\)")


def _list_cluster_custom_objects(
    client: K8sClient,
    group: str,
    version: str,
    plural: str,
) -> list[dict[str, Any]]:
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
                return []

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
def get_ingressroutes(client: K8sClient) -> list[dict[str, Any]]:
    return _list_cluster_custom_objects(
        client,
        TRAEFIK_API_GROUP,
        TRAEFIK_API_VERSION,
        "ingressroutes",
    )


@timeit
def get_ingressroutetcps(client: K8sClient) -> list[dict[str, Any]]:
    return _list_cluster_custom_objects(
        client,
        TRAEFIK_API_GROUP,
        TRAEFIK_API_VERSION,
        "ingressroutetcps",
    )


@timeit
def get_ingressrouteudps(client: K8sClient) -> list[dict[str, Any]]:
    return _list_cluster_custom_objects(
        client,
        TRAEFIK_API_GROUP,
        TRAEFIK_API_VERSION,
        "ingressrouteudps",
    )


@timeit
def get_middlewares(client: K8sClient) -> list[dict[str, Any]]:
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
    return _HOSTNAME_RE.findall(match)


def _get_middleware_type(spec: dict[str, Any]) -> str | None:
    for key in MIDDLEWARE_TYPE_KEYS:
        if key in spec:
            return key
    return None


def _collect_service_qualified_names(
    routes: list[dict[str, Any]],
    default_namespace: str,
) -> list[str]:
    seen: set[str] = set()
    for route in routes:
        for svc in route.get("services") or []:
            ns = svc.get("namespace") or default_namespace
            name = svc.get("name")
            if name and ns:
                seen.add(get_qualified_resource_name(ns, name))
    return sorted(seen)


def _collect_middleware_qualified_names(
    routes: list[dict[str, Any]],
    default_namespace: str,
) -> list[str]:
    seen: set[str] = set()
    for route in routes:
        for mw in route.get("middlewares") or []:
            ns = mw.get("namespace") or default_namespace
            name = mw.get("name")
            if name and ns:
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
            match_str = route.get("match", "")
            hostnames.extend(_extract_hostnames(match_str))

        tls = spec.get("tls") or {}

        transformed.append(
            {
                "uid": metadata["uid"],
                "name": name,
                "namespace": namespace,
                "qualified_name": get_qualified_resource_name(namespace, name),
                "entry_points": entry_points,
                "hostnames": hostnames,
                "has_tls": bool(tls),
                "tls_secret_name": tls.get("secretName"),
                "tls_cert_resolver": tls.get("certResolver"),
                "backend_service_qualified_names": (
                    _collect_service_qualified_names(routes, namespace)
                ),
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
        tls = spec.get("tls") or {}

        transformed.append(
            {
                "uid": metadata["uid"],
                "name": name,
                "namespace": namespace,
                "qualified_name": get_qualified_resource_name(namespace, name),
                "entry_points": entry_points,
                "has_tls": bool(tls),
                "tls_passthrough": tls.get("passthrough", False),
                "backend_service_qualified_names": (
                    _collect_service_qualified_names(routes, namespace)
                ),
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
                "backend_service_qualified_names": (
                    _collect_service_qualified_names(routes, namespace)
                ),
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

        middleware_type = _get_middleware_type(spec) or "unknown"

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

    if not any(
        [
            raw_ingressroutes,
            raw_ingressroutetcps,
            raw_ingressrouteudps,
            raw_middlewares,
        ]
    ):
        logger.debug("No Traefik CRDs installed on cluster %s — skipping.", client.name)
        return

    middlewares = transform_middlewares(raw_middlewares)
    ingressroutes = transform_ingressroutes(raw_ingressroutes)
    ingressroutetcps = transform_ingressroutetcps(raw_ingressroutetcps)
    ingressrouteudps = transform_ingressrouteudps(raw_ingressrouteudps)

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
