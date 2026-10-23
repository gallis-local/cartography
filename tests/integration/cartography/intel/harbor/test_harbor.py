from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.config import Config
from cartography.intel.harbor import start_harbor_ingestion
from tests.data.harbor import api
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

INSTANCE = "harbor.example.com"
NGINX = f"{INSTANCE}/library/nginx"
API = f"{INSTANCE}/team/app/api"
NGINX_IMAGE = f"{NGINX}@{api.NGINX_DIGEST}"
API_AMD64 = f"{API}@{api.API_AMD64_DIGEST}"
API_ARM64 = f"{API}@{api.API_ARM64_DIGEST}"
API_INDEX = f"{API}@{api.API_INDEX_DIGEST}"


def fake_get(url, params=None, **kwargs):
    path = url.split("/api/v2.0", 1)[1]
    if path not in api.RESPONSES:
        raise AssertionError(f"Unexpected Harbor API call: {path}")
    payload = api.RESPONSES[path]
    page = (params or {}).get("page")
    # Collections are paginated; everything fits on the first page.
    if page is not None and page > 1:
        payload = []
    return Mock(json=lambda: payload, raise_for_status=lambda: None)


def sync(neo4j_session, update_tag=1, url="https://Harbor.Example.com/"):
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        harbor_url=url,
        harbor_username="robot$cartography",
        harbor_password="secret",
    )
    config.update_tag = update_tag
    start_harbor_ingestion(neo4j_session, config)


@pytest.fixture
def synced(neo4j_session):
    with patch("requests.Session.get", side_effect=fake_get):
        sync(neo4j_session)
    return neo4j_session


def test_instance_and_projects(synced):
    assert check_nodes(synced, "HarborInstance", ["id", "url", "version"]) == {
        (INSTANCE, f"https://{INSTANCE}", "v2.11.0")
    }
    assert check_nodes(synced, "HarborProject", ["id", "name", "public"]) == {
        (f"{INSTANCE}/library", "library", True),
        (f"{INSTANCE}/team", "team", False),
    }
    assert check_rels(
        synced, "HarborInstance", "id", "HarborProject", "id", "RESOURCE"
    ) == {
        (INSTANCE, f"{INSTANCE}/library"),
        (INSTANCE, f"{INSTANCE}/team"),
    }


def test_repositories_nest_in_projects(synced):
    assert check_nodes(synced, "HarborRepository", ["id", "uri", "project_name"]) == {
        (NGINX, NGINX, "library"),
        (API, API, "team"),
    }
    assert check_rels(
        synced, "HarborProject", "id", "HarborRepository", "id", "HAS_REPOSITORY"
    ) == {
        (f"{INSTANCE}/library", NGINX),
        (f"{INSTANCE}/team", API),
    }
    # The ontology label comes from the schema, not from the test data.
    assert {row[0] for row in check_nodes(synced, "ContainerRegistry", ["id"])} >= {
        NGINX,
        API,
    }


def test_images_only_include_container_images(synced):
    assert check_nodes(synced, "HarborImage", ["id", "type", "architecture"]) == {
        (NGINX_IMAGE, "image", "amd64"),
        (API_AMD64, "image", "amd64"),
        (API_ARM64, "image", "arm64"),
        (API_INDEX, "manifest_list", None),
    }
    # Single-platform images and manifest lists get different ontology labels.
    assert check_nodes(synced, "Image", ["id"]) >= {
        (NGINX_IMAGE,),
        (API_AMD64,),
        (API_ARM64,),
    }
    assert check_nodes(synced, "ImageManifestList", ["id"]) >= {(API_INDEX,)}
    assert check_rels(
        synced, "HarborRepository", "id", "HarborImage", "id", "HAS_IMAGE"
    ) >= {(NGINX, NGINX_IMAGE), (API, API_INDEX)}
    assert check_rels(
        synced, "HarborImage", "id", "HarborImage", "id", "CONTAINS_IMAGE"
    ) == {(API_INDEX, API_AMD64), (API_INDEX, API_ARM64)}


def test_tags(synced):
    assert check_nodes(
        synced, "HarborImageTag", ["id", "name", "immutable", "signed"]
    ) == {
        (f"{NGINX}:latest", "latest", False, True),
        (f"{NGINX}:1.25", "1.25", True, False),
        (f"{API}:v1", "v1", False, False),
    }
    assert check_rels(synced, "HarborImageTag", "id", "HarborImage", "id", "IMAGE") == {
        (f"{NGINX}:latest", NGINX_IMAGE),
        (f"{NGINX}:1.25", NGINX_IMAGE),
        (f"{API}:v1", API_INDEX),
    }
    assert check_rels(
        synced, "HarborRepository", "id", "HarborImageTag", "id", "REPO_IMAGE"
    ) == {(NGINX, f"{NGINX}:latest"), (NGINX, f"{NGINX}:1.25"), (API, f"{API}:v1")}


def test_scan_state_is_recorded_even_when_not_fetched(synced):
    assert check_nodes(
        synced, "HarborImage", ["id", "scan_status", "scan_total", "sbom_status"]
    ) >= {
        (NGINX_IMAGE, "Success", 2, "Success"),
        (API_AMD64, "Running", 0, None),
        (API_ARM64, None, None, None),
    }


def test_vulnerabilities(synced):
    cve = f"{NGINX_IMAGE}|CVE-2024-0001|openssl|3.0.2"
    ghsa = f"{NGINX_IMAGE}|GHSA-xxxx-yyyy-zzzz|libfoo|1.0"
    assert check_nodes(
        synced,
        "HarborVulnerability",
        ["id", "cve_id", "severity", "fix_version", "cvss_v3_score"],
    ) == {
        (cve, "CVE-2024-0001", "HIGH", "3.0.3", 8.1),
        (ghsa, None, "LOW", None, None),
    }
    assert check_rels(
        synced, "HarborVulnerability", "id", "HarborImage", "id", "AFFECTS"
    ) == {(cve, NGINX_IMAGE), (ghsa, NGINX_IMAGE)}
    assert check_rels(
        synced, "HarborVulnerability", "id", "HarborPackage", "id", "AFFECTS"
    ) == {
        (cve, f"{NGINX_IMAGE}|openssl|3.0.2"),
        (ghsa, f"{NGINX_IMAGE}|libfoo|1.0"),
    }
    # Only the CVE-backed finding carries the CVE label.
    assert {row[0] for row in check_nodes(synced, "CVE", ["id"])} >= {cve}
    assert ghsa not in {row[0] for row in check_nodes(synced, "CVE", ["id"])}
    assert {row[0] for row in check_nodes(synced, "Risk", ["id"])} >= {cve, ghsa}


def test_sbom_packages(synced):
    openssl = f"{NGINX_IMAGE}|openssl|3.0.2"
    libfoo = f"{NGINX_IMAGE}|libfoo|1.0"
    assert check_nodes(
        synced, "HarborPackage", ["id", "type", "normalized_id", "license"]
    ) == {
        (openssl, "deb", "deb|debian/openssl|3.0.2", "Apache-2.0"),
        (libfoo, None, None, None),
    }
    assert check_rels(
        synced, "HarborPackage", "id", "HarborImage", "id", "DEPLOYED"
    ) == {(openssl, NGINX_IMAGE), (libfoo, NGINX_IMAGE)}


def test_cleanup_removes_what_disappeared(neo4j_session):
    with patch("requests.Session.get", side_effect=fake_get):
        sync(neo4j_session, update_tag=1)

    shrunk = {
        **api.RESPONSES,
        "/projects/library/repositories/nginx/artifacts": [],
    }
    with (
        patch.dict(api.RESPONSES, shrunk),
        patch("requests.Session.get", side_effect=fake_get),
    ):
        sync(neo4j_session, update_tag=2)

    images = {row[0] for row in check_nodes(neo4j_session, "HarborImage", ["id"])}
    assert NGINX_IMAGE not in images
    assert API_INDEX in images
    assert check_nodes(neo4j_session, "HarborVulnerability", ["id"]) == set()
    assert check_nodes(neo4j_session, "HarborPackage", ["id"]) == set()
    # The instance and the repositories it still lists are retained.
    assert check_nodes(neo4j_session, "HarborInstance", ["id"]) == {(INSTANCE,)}


def test_unconfigured_module_is_skipped(neo4j_session):
    config = Config(neo4j_uri="bolt://localhost:7687")
    config.update_tag = 1
    with patch("requests.Session.get") as mock_get:
        start_harbor_ingestion(neo4j_session, config)
    mock_get.assert_not_called()
