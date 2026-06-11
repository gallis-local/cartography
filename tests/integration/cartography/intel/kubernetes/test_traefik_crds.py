from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

import pytest
from kubernetes.client.exceptions import ApiException

import cartography.intel.kubernetes.traefik_crds
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.services import load_services
from cartography.intel.kubernetes.traefik_crds import load_ingressroutes
from cartography.intel.kubernetes.traefik_crds import load_ingressroutetcps
from cartography.intel.kubernetes.traefik_crds import load_ingressrouteudps
from cartography.intel.kubernetes.traefik_crds import load_middlewares
from cartography.intel.kubernetes.traefik_crds import sync_traefik_crds
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACES_DATA
from tests.data.kubernetes.services import KUBERNETES_SERVICES_DATA
from tests.data.kubernetes.traefik_crds import TRAEFIK_INGRESSROUTES_DATA
from tests.data.kubernetes.traefik_crds import TRAEFIK_INGRESSROUTES_RAW
from tests.data.kubernetes.traefik_crds import TRAEFIK_INGRESSROUTETCPS_DATA
from tests.data.kubernetes.traefik_crds import TRAEFIK_INGRESSROUTETCPS_RAW
from tests.data.kubernetes.traefik_crds import TRAEFIK_INGRESSROUTEUDPS_DATA
from tests.data.kubernetes.traefik_crds import TRAEFIK_INGRESSROUTEUDPS_RAW
from tests.data.kubernetes.traefik_crds import TRAEFIK_MIDDLEWARES_DATA
from tests.data.kubernetes.traefik_crds import TRAEFIK_MIDDLEWARES_RAW
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _create_test_cluster(neo4j_session):
    load_kubernetes_cluster(
        neo4j_session,
        KUBERNETES_CLUSTER_DATA,
        TEST_UPDATE_TAG,
    )
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_2_NAMESPACES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[1],
        cluster_name=KUBERNETES_CLUSTER_NAMES[1],
    )
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )


def _cleanup_test_cluster(neo4j_session):
    for label in [
        "TraefikIngressRoute",
        "TraefikIngressRouteTCP",
        "TraefikIngressRouteUDP",
        "TraefikMiddleware",
        "KubernetesService",
        "KubernetesNamespace",
        "KubernetesCluster",
    ]:
        neo4j_session.run(f"MATCH (n:{label}) DETACH DELETE n")


def test_load_traefik_ingressroutes(neo4j_session):
    _create_test_cluster(neo4j_session)

    try:
        load_ingressroutes(
            neo4j_session,
            TRAEFIK_INGRESSROUTES_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        assert check_nodes(neo4j_session, "TraefikIngressRoute", ["name"]) == {
            ("my-ingressroute",),
        }
    finally:
        _cleanup_test_cluster(neo4j_session)


def test_load_traefik_ingressroutetcps(neo4j_session):
    _create_test_cluster(neo4j_session)

    try:
        load_ingressroutetcps(
            neo4j_session,
            TRAEFIK_INGRESSROUTETCPS_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        assert check_nodes(neo4j_session, "TraefikIngressRouteTCP", ["name"]) == {
            ("my-tcp-route",),
        }
    finally:
        _cleanup_test_cluster(neo4j_session)


def test_load_traefik_ingressrouteudps(neo4j_session):
    _create_test_cluster(neo4j_session)

    try:
        load_ingressrouteudps(
            neo4j_session,
            TRAEFIK_INGRESSROUTEUDPS_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        assert check_nodes(neo4j_session, "TraefikIngressRouteUDP", ["name"]) == {
            ("my-udp-route",),
        }
    finally:
        _cleanup_test_cluster(neo4j_session)


def test_load_traefik_middlewares(neo4j_session):
    _create_test_cluster(neo4j_session)

    try:
        load_middlewares(
            neo4j_session,
            TRAEFIK_MIDDLEWARES_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        assert check_nodes(neo4j_session, "TraefikMiddleware", ["name"]) == {
            ("my-middleware",),
        }
    finally:
        _cleanup_test_cluster(neo4j_session)


def test_traefik_relationships(neo4j_session):
    _create_test_cluster(neo4j_session)

    try:
        load_middlewares(
            neo4j_session,
            TRAEFIK_MIDDLEWARES_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_ingressroutes(
            neo4j_session,
            TRAEFIK_INGRESSROUTES_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_ingressroutetcps(
            neo4j_session,
            TRAEFIK_INGRESSROUTETCPS_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_ingressrouteudps(
            neo4j_session,
            TRAEFIK_INGRESSROUTEUDPS_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        assert check_rels(
            neo4j_session,
            "TraefikIngressRoute",
            "name",
            "KubernetesCluster",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ) == {("my-ingressroute", KUBERNETES_CLUSTER_IDS[0])}

        assert check_rels(
            neo4j_session,
            "TraefikIngressRoute",
            "name",
            "KubernetesNamespace",
            "name",
            "CONTAINS",
            rel_direction_right=False,
        ) == {("my-ingressroute", "my-namespace")}

        assert check_rels(
            neo4j_session,
            "TraefikIngressRoute",
            "name",
            "KubernetesService",
            "name",
            "TARGETS",
            rel_direction_right=True,
        ) == {
            ("my-ingressroute", "api-service"),
            ("my-ingressroute", "app-service"),
        }

        assert check_rels(
            neo4j_session,
            "TraefikIngressRoute",
            "name",
            "TraefikMiddleware",
            "name",
            "USES_MIDDLEWARE",
            rel_direction_right=True,
        ) == {("my-ingressroute", "my-middleware")}

        assert check_rels(
            neo4j_session,
            "TraefikIngressRouteTCP",
            "name",
            "KubernetesService",
            "name",
            "TARGETS",
            rel_direction_right=True,
        ) == {("my-tcp-route", "api-service")}

        assert check_rels(
            neo4j_session,
            "TraefikIngressRouteUDP",
            "name",
            "KubernetesService",
            "name",
            "TARGETS",
            rel_direction_right=True,
        ) == {("my-udp-route", "app-service")}

    finally:
        _cleanup_test_cluster(neo4j_session)


@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutes")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutetcps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressrouteudps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_middlewares")
def test_sync_traefik_crds_end_to_end(
    mock_get_middlewares,
    mock_get_ingressrouteudps,
    mock_get_ingressroutetcps,
    mock_get_ingressroutes,
    neo4j_session,
):
    _create_test_cluster(neo4j_session)

    try:
        namespace = KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"]
        false_match_service = {
            "uid": uuid4().hex,
            "name": "not-a-service",
            "qualified_name": f"{namespace}/not-a-service",
            "creation_timestamp": 1633581720,
            "deletion_timestamp": None,
            "namespace": namespace,
            "type": "ClusterIP",
            "selector": "{}",
            "cluster_ip": "10.0.2.3",
            "pod_ids": [],
            "load_balancer_ip": None,
        }
        load_services(
            neo4j_session,
            [false_match_service],
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        mock_get_middlewares.return_value = deepcopy(TRAEFIK_MIDDLEWARES_RAW)
        mock_get_ingressroutes.return_value = deepcopy(TRAEFIK_INGRESSROUTES_RAW)
        mock_get_ingressroutetcps.return_value = deepcopy(TRAEFIK_INGRESSROUTETCPS_RAW)
        mock_get_ingressrouteudps.return_value = deepcopy(TRAEFIK_INGRESSROUTEUDPS_RAW)

        k8s_client = MagicMock()
        k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]

        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
        }

        sync_traefik_crds(
            neo4j_session=neo4j_session,
            client=k8s_client,
            update_tag=TEST_UPDATE_TAG,
            common_job_parameters=common_job_parameters,
        )

        assert check_nodes(neo4j_session, "TraefikIngressRoute", ["name"]) == {
            ("my-ingressroute",),
        }
        assert check_nodes(neo4j_session, "TraefikIngressRouteTCP", ["name"]) == {
            ("my-tcp-route",),
        }
        assert check_nodes(neo4j_session, "TraefikIngressRouteUDP", ["name"]) == {
            ("my-udp-route",),
        }
        assert check_nodes(neo4j_session, "TraefikMiddleware", ["name"]) == {
            ("my-middleware",),
        }

        assert check_rels(
            neo4j_session,
            "TraefikIngressRoute",
            "name",
            "KubernetesService",
            "name",
            "TARGETS",
            rel_direction_right=True,
        ) == {
            ("my-ingressroute", "api-service"),
            ("my-ingressroute", "app-service"),
        }

    finally:
        _cleanup_test_cluster(neo4j_session)


@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutes")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutetcps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressrouteudps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_middlewares")
def test_sync_traefik_crds_cleans_up_stale_nodes_and_rels(
    mock_get_middlewares,
    mock_get_ingressrouteudps,
    mock_get_ingressroutetcps,
    mock_get_ingressroutes,
    neo4j_session,
):
    _create_test_cluster(neo4j_session)

    try:
        namespace = KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"]
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
        }
        k8s_client = MagicMock()
        k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]

        first_middlewares = deepcopy(TRAEFIK_MIDDLEWARES_RAW)
        first_routes = deepcopy(TRAEFIK_INGRESSROUTES_RAW) + [
            {
                "apiVersion": "traefik.io/v1alpha1",
                "kind": "IngressRoute",
                "metadata": {
                    "name": "stale-ingressroute",
                    "namespace": namespace,
                    "uid": "ir-uid-stale-1",
                    "creationTimestamp": "2021-10-07T06:21:06Z",
                },
                "spec": {
                    "entryPoints": ["web"],
                    "routes": [
                        {
                            "match": "Host(`stale.example.com`)",
                            "kind": "Rule",
                            "services": [{"name": "api-service", "port": 80}],
                        },
                    ],
                },
            },
        ]

        mock_get_middlewares.return_value = first_middlewares
        mock_get_ingressroutes.return_value = first_routes
        mock_get_ingressroutetcps.return_value = deepcopy(TRAEFIK_INGRESSROUTETCPS_RAW)
        mock_get_ingressrouteudps.return_value = deepcopy(TRAEFIK_INGRESSROUTEUDPS_RAW)

        sync_traefik_crds(
            neo4j_session=neo4j_session,
            client=k8s_client,
            update_tag=TEST_UPDATE_TAG,
            common_job_parameters=common_job_parameters,
        )

        assert check_nodes(neo4j_session, "TraefikIngressRoute", ["name"]) == {
            ("my-ingressroute",),
            ("stale-ingressroute",),
        }

        next_update_tag = TEST_UPDATE_TAG + 1
        common_job_parameters["UPDATE_TAG"] = next_update_tag
        mock_get_middlewares.return_value = deepcopy(TRAEFIK_MIDDLEWARES_RAW)
        mock_get_ingressroutes.return_value = deepcopy(TRAEFIK_INGRESSROUTES_RAW)
        mock_get_ingressroutetcps.return_value = deepcopy(TRAEFIK_INGRESSROUTETCPS_RAW)
        mock_get_ingressrouteudps.return_value = deepcopy(TRAEFIK_INGRESSROUTEUDPS_RAW)

        sync_traefik_crds(
            neo4j_session=neo4j_session,
            client=k8s_client,
            update_tag=next_update_tag,
            common_job_parameters=common_job_parameters,
        )

        assert check_nodes(neo4j_session, "TraefikIngressRoute", ["name"]) == {
            ("my-ingressroute",),
        }
        assert check_nodes(neo4j_session, "TraefikIngressRouteTCP", ["name"]) == {
            ("my-tcp-route",),
        }
        assert check_nodes(neo4j_session, "TraefikIngressRouteUDP", ["name"]) == {
            ("my-udp-route",),
        }
        assert check_nodes(neo4j_session, "TraefikMiddleware", ["name"]) == {
            ("my-middleware",),
        }

    finally:
        _cleanup_test_cluster(neo4j_session)


@pytest.mark.parametrize("status", [401, 403])
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutes")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutetcps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressrouteudps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_middlewares")
def test_sync_traefik_crds_preserves_existing_data_on_permission_error(
    mock_get_middlewares,
    mock_get_ingressrouteudps,
    mock_get_ingressroutetcps,
    mock_get_ingressroutes,
    status,
    neo4j_session,
):
    _create_test_cluster(neo4j_session)

    try:
        load_middlewares(
            neo4j_session,
            TRAEFIK_MIDDLEWARES_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_ingressroutes(
            neo4j_session,
            TRAEFIK_INGRESSROUTES_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_ingressroutetcps(
            neo4j_session,
            TRAEFIK_INGRESSROUTETCPS_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )
        load_ingressrouteudps(
            neo4j_session,
            TRAEFIK_INGRESSROUTEUDPS_DATA,
            update_tag=TEST_UPDATE_TAG,
            cluster_id=KUBERNETES_CLUSTER_IDS[0],
            cluster_name=KUBERNETES_CLUSTER_NAMES[0],
        )

        mock_get_ingressroutes.side_effect = ApiException(status=status)

        k8s_client = MagicMock()
        k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]

        sync_traefik_crds(
            neo4j_session=neo4j_session,
            client=k8s_client,
            update_tag=TEST_UPDATE_TAG + 1,
            common_job_parameters={
                "UPDATE_TAG": TEST_UPDATE_TAG + 1,
                "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
            },
        )

        assert check_nodes(neo4j_session, "TraefikIngressRoute", ["name"]) == {
            ("my-ingressroute",),
        }
        assert check_nodes(neo4j_session, "TraefikIngressRouteTCP", ["name"]) == {
            ("my-tcp-route",),
        }
        assert check_nodes(neo4j_session, "TraefikIngressRouteUDP", ["name"]) == {
            ("my-udp-route",),
        }
        assert check_nodes(neo4j_session, "TraefikMiddleware", ["name"]) == {
            ("my-middleware",),
        }

    finally:
        _cleanup_test_cluster(neo4j_session)
