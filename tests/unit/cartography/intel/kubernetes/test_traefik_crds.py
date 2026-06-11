from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kubernetes.client.exceptions import ApiException

import cartography.intel.kubernetes.traefik_crds
from cartography.intel.kubernetes.traefik_crds import _list_cluster_custom_objects
from cartography.intel.kubernetes.traefik_crds import sync_traefik_crds
from cartography.intel.kubernetes.traefik_crds import transform_ingressroutes
from cartography.intel.kubernetes.traefik_crds import transform_middlewares
from tests.data.kubernetes.traefik_crds import TRAEFIK_INGRESSROUTES_DATA
from tests.data.kubernetes.traefik_crds import TRAEFIK_INGRESSROUTES_RAW
from tests.data.kubernetes.traefik_crds import TRAEFIK_MIDDLEWARES_RAW


def test_list_cluster_custom_objects_returns_empty_on_missing_crd():
    client = MagicMock()
    client.name = "test-cluster"
    client.custom.list_cluster_custom_object.side_effect = ApiException(status=404)

    resources = _list_cluster_custom_objects(
        client,
        group="traefik.io",
        version="v1alpha1",
        plural="ingressroutes",
    )

    assert resources == []


@pytest.mark.parametrize("status", [401, 403, 500])
def test_list_cluster_custom_objects_raises_on_non_404_errors(status):
    client = MagicMock()
    client.name = "test-cluster"
    client.custom.list_cluster_custom_object.side_effect = ApiException(status=status)

    with pytest.raises(ApiException):
        _list_cluster_custom_objects(
            client,
            group="traefik.io",
            version="v1alpha1",
            plural="ingressroutes",
        )


@pytest.mark.parametrize("status", [401, 403])
@patch.object(cartography.intel.kubernetes.traefik_crds, "cleanup")
@patch.object(cartography.intel.kubernetes.traefik_crds, "load_middlewares")
@patch.object(cartography.intel.kubernetes.traefik_crds, "load_ingressrouteudps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "load_ingressroutetcps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "load_ingressroutes")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_middlewares")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressrouteudps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutetcps")
@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutes")
def test_sync_traefik_crds_skips_load_and_cleanup_on_permission_error(
    mock_get_ingressroutes,
    mock_get_ingressroutetcps,
    mock_get_ingressrouteudps,
    mock_get_middlewares,
    mock_load_ingressroutes,
    mock_load_ingressroutetcps,
    mock_load_ingressrouteudps,
    mock_load_middlewares,
    mock_cleanup,
    status,
    caplog,
):
    mock_get_ingressroutes.side_effect = ApiException(status=status)
    neo4j_session = MagicMock()
    client = MagicMock()
    client.name = "test-cluster"

    with caplog.at_level("WARNING", logger="cartography.intel.kubernetes.traefik_crds"):
        sync_traefik_crds(
            neo4j_session=neo4j_session,
            client=client,
            update_tag=1,
            common_job_parameters={"UPDATE_TAG": 1, "CLUSTER_ID": "cid"},
        )

    mock_load_ingressroutes.assert_not_called()
    mock_load_ingressroutetcps.assert_not_called()
    mock_load_ingressrouteudps.assert_not_called()
    mock_load_middlewares.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any("test-cluster" in record.message for record in caplog.records)


@patch.object(cartography.intel.kubernetes.traefik_crds, "get_ingressroutes")
def test_sync_traefik_crds_propagates_unexpected_api_errors(mock_get_ingressroutes):
    mock_get_ingressroutes.side_effect = ApiException(status=500)
    with pytest.raises(ApiException):
        sync_traefik_crds(
            neo4j_session=MagicMock(),
            client=MagicMock(name="test-cluster"),
            update_tag=1,
            common_job_parameters={"UPDATE_TAG": 1, "CLUSTER_ID": "cid"},
        )


def test_transform_ingressroutes_extracts_hostnames():
    transformed = transform_ingressroutes(TRAEFIK_INGRESSROUTES_RAW)

    assert len(transformed) == 1
    assert transformed[0]["hostnames"] == ["app.example.com"]


def test_transform_ingressroutes_requires_required_metadata_fields():
    items = [
        {"metadata": {"uid": "ir-uid", "namespace": "default"}, "spec": {"routes": []}},
    ]

    with pytest.raises(KeyError):
        transform_ingressroutes(items)


def test_transform_ingressroutes_normalizes_rfc3339_timestamps_to_epoch():
    [transformed] = transform_ingressroutes(TRAEFIK_INGRESSROUTES_RAW)

    assert transformed["creation_timestamp"] == 1633587666


def test_transform_ingressroutes_sets_tls_fields():
    [transformed] = transform_ingressroutes(TRAEFIK_INGRESSROUTES_RAW)

    assert transformed["has_tls"] is True
    assert transformed["tls_secret_name"] == "my-tls-secret"
    assert transformed["tls_cert_resolver"] == "letsencrypt"


def test_transform_ingressroutes_no_tls():
    raw_no_tls = [
        {
            "apiVersion": "traefik.io/v1alpha1",
            "kind": "IngressRoute",
            "metadata": {
                "name": "no-tls-route",
                "namespace": "default",
                "uid": "ir-uid-no-tls",
                "creationTimestamp": "2021-10-07T06:21:06+00:00",
            },
            "spec": {
                "entryPoints": ["web"],
                "routes": [
                    {
                        "match": "Host(`example.com`)",
                        "kind": "Rule",
                        "services": [{"name": "svc", "port": 80}],
                    }
                ],
            },
        },
    ]

    [transformed] = transform_ingressroutes(raw_no_tls)

    assert transformed["has_tls"] is False
    assert transformed["tls_secret_name"] is None
    assert transformed["tls_cert_resolver"] is None


def test_transform_ingressroutes_sets_qualified_names():
    [transformed] = transform_ingressroutes(TRAEFIK_INGRESSROUTES_RAW)

    ns = transformed["namespace"]
    assert transformed["qualified_name"] == f"{ns}/my-ingressroute"
    assert f"{ns}/api-service" in transformed["backend_service_qualified_names"]
    assert f"{ns}/app-service" in transformed["backend_service_qualified_names"]
    assert f"{ns}/my-middleware" in transformed["middleware_qualified_names"]


def test_transform_middlewares_detects_type():
    [transformed] = transform_middlewares(TRAEFIK_MIDDLEWARES_RAW)

    assert transformed["middleware_type"] == "forwardAuth"


def test_transform_middlewares_returns_unknown_for_no_match():
    raw_unknown = [
        {
            "apiVersion": "traefik.io/v1alpha1",
            "kind": "Middleware",
            "metadata": {
                "name": "unknown-mw",
                "namespace": "default",
                "uid": "mw-uid-unknown",
                "creationTimestamp": "2021-10-07T06:20:00+00:00",
            },
            "spec": {"someFutureType": {"setting": "value"}},
        },
    ]

    [transformed] = transform_middlewares(raw_unknown)

    assert transformed["middleware_type"] == "unknown"


def test_sync_traefik_crds_skips_when_no_cluster_id(caplog):
    neo4j_session = MagicMock()
    client = MagicMock()
    client.name = "test-cluster"

    sync_traefik_crds(
        neo4j_session=neo4j_session,
        client=client,
        update_tag=1,
        common_job_parameters={"UPDATE_TAG": 1},
    )

    assert any("No CLUSTER_ID" in record.message for record in caplog.records)
