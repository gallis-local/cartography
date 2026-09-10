from copy import deepcopy
from math import ceil
from typing import Any
from urllib.parse import parse_qsl
from urllib.parse import urlencode
from urllib.parse import urlparse

import pytest

import cartography.intel.prowler
from cartography.config import Config
from tests.data.prowler import API_KEY
from tests.data.prowler import API_URL
from tests.data.prowler import AWS_ACCOUNT_ID
from tests.data.prowler import CVE_ID
from tests.data.prowler import FINDING_BUCKET_ENCRYPTED_ID
from tests.data.prowler import FINDING_BUCKET_ENCRYPTED_UID
from tests.data.prowler import FINDING_BUCKET_PUBLIC_ID
from tests.data.prowler import FINDING_BUCKET_PUBLIC_UID
from tests.data.prowler import FINDING_IAM_USER_ID
from tests.data.prowler import FINDING_IAM_USER_UID
from tests.data.prowler import FINDINGS
from tests.data.prowler import GITHUB_ORG_UID
from tests.data.prowler import KUBERNETES_CLUSTER_NAME
from tests.data.prowler import PROVIDER_AWS_ID
from tests.data.prowler import PROVIDER_GITHUB_ID
from tests.data.prowler import PROVIDER_KUBERNETES_ID
from tests.data.prowler import PROVIDERS
from tests.data.prowler import RESOURCE_BUCKET_ID
from tests.data.prowler import RESOURCE_BUCKET_UID
from tests.data.prowler import RESOURCE_IAM_USER_ID
from tests.data.prowler import RESOURCE_IAM_USER_UID
from tests.data.prowler import RESOURCE_INSTANCE_ID
from tests.data.prowler import RESOURCE_INSTANCE_UID
from tests.data.prowler import RESOURCES
from tests.data.prowler import SCAN_AWS_ID
from tests.data.prowler import SCAN_GITHUB_ID
from tests.data.prowler import SCANS
from tests.data.prowler import TENANT_ID
from tests.data.prowler import TENANT_NAME
from tests.data.prowler import TENANTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789

SYNC_METADATA_ID = f"ProwlerTenant_{TENANT_ID}_ProwlerData"

# Every collection the module reads, keyed by the path the fake serves it on.
COLLECTION_BY_PATH = {
    "/api/v1/tenants": "tenants",
    "/api/v1/providers": "providers",
    "/api/v1/scans": "scans",
    "/api/v1/resources/latest": "resources",
    "/api/v1/findings/latest": "findings",
}
DEFAULT_PAGE_SIZE = 100

PROWLER_LABELS = (
    "ProwlerTenant",
    "ProwlerProvider",
    "ProwlerScan",
    "ProwlerResource",
    "ProwlerFinding",
)


class FakeProwlerApi:
    """A stateful fake of the Prowler JSON:API, patched in at the HTTP boundary.

    It implements real JSON:API pagination: `links.next` is an absolute URL that
    carries the whole query string, and each page has a distinct URL, so the
    module's own `iter_pages` / `iter_resources` code does the paging for real.
    """

    def __init__(self) -> None:
        self.state: dict[str, list[dict[str, Any]]] = {
            "tenants": deepcopy(TENANTS),
            "providers": deepcopy(PROVIDERS),
            "scans": deepcopy(SCANS),
            "resources": deepcopy(RESOURCES),
            "findings": deepcopy(FINDINGS),
        }
        self.page_sizes: dict[str, int] = {}
        self.fail_on: tuple[str, int] | None = None
        self.requested_pages: list[tuple[str, int]] = []

    def remove(self, collection: str, object_id: str) -> None:
        """Drop one object from the fake's state, as Prowler would on deletion."""
        rows = self.state[collection]
        remaining = [row for row in rows if row["id"] != object_id]
        assert len(remaining) == len(rows) - 1, f"{object_id} not in {collection}"
        self.state[collection] = remaining

    def _sideloaded_resources(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        wanted: list[str] = []
        for finding in findings:
            entries = finding["relationships"]["resources"]["data"]
            for entry in entries:
                if entry["id"] not in wanted:
                    wanted.append(entry["id"])
        by_id = {resource["id"]: resource for resource in self.state["resources"]}
        return [deepcopy(by_id[uuid]) for uuid in wanted if uuid in by_id]

    def __call__(
        self,
        session: Any,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        redact_path: str | None = None,
    ) -> dict[str, Any]:
        assert method == "GET", f"Unexpected Prowler request method {method}"
        assert json_body is None
        parsed = urlparse(url)
        assert f"{parsed.scheme}://{parsed.netloc}" == API_URL
        collection = COLLECTION_BY_PATH.get(parsed.path)
        if collection is None:
            raise AssertionError(f"Unexpected Prowler path {parsed.path}")

        query = dict(parse_qsl(parsed.query))
        if params is not None:
            # `page[size]` is only sent on the first request of a collection.
            assert not parsed.query, "the first request must not carry a query string"
            assert params["page[size]"] == 100
            query.update({key: str(value) for key, value in params.items()})
        else:
            assert parsed.query, "a followed next link must carry its query string"
        if collection == "findings":
            assert query.get("include") == "resources"

        page_number = int(query.get("page[number]", 1))
        self.requested_pages.append((collection, page_number))
        if self.fail_on == (collection, page_number):
            raise RuntimeError(
                f"synthetic Prowler {collection} page {page_number} failure",
            )

        rows = self.state[collection]
        page_size = self.page_sizes.get(collection, DEFAULT_PAGE_SIZE)
        page_count = max(1, ceil(len(rows) / page_size))
        start = (page_number - 1) * page_size
        page_rows = deepcopy(rows[start : start + page_size])

        next_url = None
        if page_number < page_count:
            next_query = dict(query)
            next_query["page[number]"] = str(page_number + 1)
            next_url = f"{API_URL}{parsed.path}?{urlencode(next_query)}"

        document: dict[str, Any] = {
            "data": page_rows,
            "meta": {
                "pagination": {
                    "page": page_number,
                    "pages": page_count,
                    "count": len(rows),
                },
            },
            "links": {
                "first": f"{API_URL}{parsed.path}?page%5Bnumber%5D=1",
                "last": f"{API_URL}{parsed.path}?page%5Bnumber%5D={page_count}",
                "next": next_url,
                "prev": None,
            },
        }
        if collection == "findings":
            document["included"] = self._sideloaded_resources(page_rows)
        return document


@pytest.fixture(autouse=True)
def cleanup_prowler_test_data(neo4j_session):
    label_predicate = " OR ".join(f"n:{label}" for label in PROWLER_LABELS)
    cleanup_query = f"MATCH (n) WHERE {label_predicate} DETACH DELETE n"

    def _cleanup() -> None:
        neo4j_session.run(cleanup_query)
        neo4j_session.run(
            "MATCH (n:AWSAccount {id: $account_id}) DETACH DELETE n",
            account_id=AWS_ACCOUNT_ID,
        )
        neo4j_session.run(
            "MATCH (n:KubernetesCluster {name: $name}) DETACH DELETE n",
            name=KUBERNETES_CLUSTER_NAME,
        )
        neo4j_session.run(
            "MATCH (n:ModuleSyncMetadata {id: $metadata_id}) DETACH DELETE n",
            metadata_id=SYNC_METADATA_ID,
        )

    _cleanup()
    yield
    _cleanup()


def _config(update_tag: int = TEST_UPDATE_TAG) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        prowler_api_url=API_URL,
        prowler_api_key=API_KEY,
        prowler_tenant_id=TENANT_ID,
    )


def _patch_prowler_api(mocker) -> FakeProwlerApi:
    fake = FakeProwlerApi()
    mocker.patch(
        "cartography.intel.prowler.api._request_json",
        side_effect=fake,
    )
    return fake


def _seed_aws_account(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (a:AWSAccount {id: $account_id})
        SET a.lastupdated = $update_tag
        """,
        account_id=AWS_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _seed_kubernetes_cluster(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (c:KubernetesCluster {name: $name})
        SET c.id = $name, c.lastupdated = $update_tag
        """,
        name=KUBERNETES_CLUSTER_NAME,
        update_tag=TEST_UPDATE_TAG,
    )


def _list_property(neo4j_session, label: str, node_id: str, prop: str) -> Any:
    """Read one list-valued property, which check_nodes() cannot put in a set."""
    record = neo4j_session.run(
        f"MATCH (n:{label} {{id: $node_id}}) RETURN n.{prop} AS value",
        node_id=node_id,
    ).single()
    assert record is not None, f"{label} {node_id} not found"
    return record["value"]


def _node_count(neo4j_session, label: str) -> int:
    return neo4j_session.run(
        f"MATCH (n:{label}) RETURN count(n) AS count",
    ).single()["count"]


def _rel_count(neo4j_session, rel_label: str) -> int:
    return neo4j_session.run(
        f"""
        MATCH (n1)-[r:{rel_label}]->(n2)
        WHERE (n1:ProwlerTenant OR n1:ProwlerProvider OR n1:ProwlerScan
               OR n1:ProwlerFinding)
        RETURN count(r) AS count
        """,
    ).single()["count"]


def _sync_metadata_lastupdated(neo4j_session) -> Any:
    record = neo4j_session.run(
        "MATCH (n:ModuleSyncMetadata {id: $id}) RETURN n.lastupdated AS lastupdated",
        id=SYNC_METADATA_ID,
    ).single()
    assert record is not None
    return record["lastupdated"]


def test_start_prowler_ingestion_loads_the_full_graph(neo4j_session, mocker):
    # Arrange
    _patch_prowler_api(mocker)

    # Act
    cartography.intel.prowler.start_prowler_ingestion(neo4j_session, _config())

    # Assert: the tenant, including its Tenant ontology label and fields.
    assert check_nodes(
        neo4j_session,
        "ProwlerTenant",
        ["id", "name", "api_url", "_ont_name", "_ont_source"],
    ) == {(TENANT_ID, TENANT_NAME, API_URL, TENANT_NAME, "prowler")}
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name"]) == {
        (TENANT_ID, TENANT_NAME),
    }

    # Assert: providers, with only the matching cloud-link field populated.
    assert check_nodes(
        neo4j_session,
        "ProwlerProvider",
        [
            "id",
            "uid",
            "provider_type",
            "alias",
            "available",
            "connected",
            "is_dynamic",
            "is_imported",
            "aws_account_id",
            "azure_subscription_id",
            "gcp_project_id",
            "kubernetes_cluster_name",
        ],
    ) == {
        (
            PROVIDER_AWS_ID,
            AWS_ACCOUNT_ID,
            "aws",
            "synthetic-aws-production",
            True,
            True,
            False,
            False,
            AWS_ACCOUNT_ID,
            None,
            None,
            None,
        ),
        (
            PROVIDER_KUBERNETES_ID,
            KUBERNETES_CLUSTER_NAME,
            "kubernetes",
            "synthetic-kubernetes",
            True,
            False,
            False,
            False,
            None,
            None,
            None,
            KUBERNETES_CLUSTER_NAME,
        ),
        (
            PROVIDER_GITHUB_ID,
            GITHUB_ORG_UID,
            "github",
            None,
            True,
            True,
            True,
            False,
            None,
            None,
            None,
            None,
        ),
    }

    # Assert: scans.
    assert check_nodes(
        neo4j_session,
        "ProwlerScan",
        [
            "id",
            "name",
            "trigger",
            "state",
            "unique_resource_count",
            "progress",
            "duration",
            "provider_id",
        ],
    ) == {
        (
            SCAN_AWS_ID,
            "synthetic-aws-daily",
            "scheduled",
            "completed",
            3,
            100,
            412,
            PROVIDER_AWS_ID,
        ),
        (
            SCAN_GITHUB_ID,
            "synthetic-github-manual",
            "manual",
            "executing",
            0,
            35,
            None,
            PROVIDER_GITHUB_ID,
        ),
    }

    # Assert: resources.
    assert check_nodes(
        neo4j_session,
        "ProwlerResource",
        [
            "id",
            "uid",
            "name",
            "region",
            "service",
            "resource_type",
            "partition",
            "failed_findings_count",
            "provider_id",
        ],
    ) == {
        (
            RESOURCE_BUCKET_ID,
            RESOURCE_BUCKET_UID,
            "synthetic-prowler-bucket",
            "us-west-2",
            "s3",
            "AwsS3Bucket",
            "aws",
            1,
            PROVIDER_AWS_ID,
        ),
        (
            RESOURCE_INSTANCE_ID,
            RESOURCE_INSTANCE_UID,
            "synthetic-app-server",
            "us-west-2",
            "ec2",
            "AwsEc2Instance",
            "aws",
            1,
            PROVIDER_AWS_ID,
        ),
        (
            RESOURCE_IAM_USER_ID,
            RESOURCE_IAM_USER_UID,
            "synthetic-user",
            "us-east-1",
            "iam",
            "AwsIamUser",
            "aws",
            1,
            PROVIDER_AWS_ID,
        ),
    }
    # The tag map is flattened into two sorted string lists.
    assert _list_property(
        neo4j_session,
        "ProwlerResource",
        RESOURCE_BUCKET_ID,
        "tag_keys",
    ) == ["env", "owner"]
    assert _list_property(
        neo4j_session,
        "ProwlerResource",
        RESOURCE_BUCKET_ID,
        "tags",
    ) == ["env=prod", "owner=security"]
    assert _list_property(
        neo4j_session,
        "ProwlerResource",
        RESOURCE_BUCKET_ID,
        "groups",
    ) == ["storage"]
    # An empty tag map and an empty group list leave the properties unset.
    assert (
        _list_property(
            neo4j_session,
            "ProwlerResource",
            RESOURCE_IAM_USER_ID,
            "tag_keys",
        )
        is None
    )
    assert (
        _list_property(
            neo4j_session,
            "ProwlerResource",
            RESOURCE_IAM_USER_ID,
            "groups",
        )
        is None
    )

    # Assert: findings.
    assert check_nodes(
        neo4j_session,
        "ProwlerFinding",
        [
            "id",
            "uid",
            "check_id",
            "check_title",
            "status",
            "severity",
            "delta",
            "service_name",
            "resource_type",
            "resource_groups",
            "muted",
            "muted_reason",
            "triage_status",
            "scan_id",
        ],
    ) == {
        (
            FINDING_BUCKET_PUBLIC_ID,
            FINDING_BUCKET_PUBLIC_UID,
            "s3_bucket_public_access",
            "Ensure S3 buckets are not publicly accessible",
            "FAIL",
            "critical",
            "new",
            "s3",
            "AwsS3Bucket",
            "storage",
            False,
            None,
            "open",
            SCAN_AWS_ID,
        ),
        (
            FINDING_BUCKET_ENCRYPTED_ID,
            FINDING_BUCKET_ENCRYPTED_UID,
            "s3_bucket_default_encryption",
            "Ensure S3 buckets have default encryption enabled",
            "PASS",
            "informational",
            None,
            "s3",
            "AwsS3Bucket",
            "storage",
            True,
            "Accepted by the storage team.",
            "risk_accepted",
            SCAN_AWS_ID,
        ),
        (
            FINDING_IAM_USER_ID,
            FINDING_IAM_USER_UID,
            "iam_user_mfa_enabled",
            "Ensure IAM users have MFA enabled",
            "FAIL",
            "medium",
            "changed",
            "iam",
            "AwsIamUser",
            "identity",
            False,
            None,
            "resolved",
            SCAN_AWS_ID,
        ),
    }
    assert _list_property(
        neo4j_session,
        "ProwlerFinding",
        FINDING_BUCKET_PUBLIC_ID,
        "compliance_frameworks",
    ) == ["CIS-2.0", "SOC2"]
    assert _list_property(
        neo4j_session,
        "ProwlerFinding",
        FINDING_BUCKET_PUBLIC_ID,
        "categories",
    ) == ["internet-exposed"]
    assert sorted(
        _list_property(
            neo4j_session,
            "ProwlerFinding",
            FINDING_BUCKET_PUBLIC_ID,
            "resource_uids",
        ),
    ) == sorted([RESOURCE_BUCKET_UID, RESOURCE_INSTANCE_UID])
    assert _list_property(
        neo4j_session,
        "ProwlerFinding",
        FINDING_IAM_USER_ID,
        "cve_ids",
    ) == [CVE_ID]
    assert (
        _list_property(
            neo4j_session,
            "ProwlerFinding",
            FINDING_BUCKET_ENCRYPTED_ID,
            "categories",
        )
        is None
    )

    # Assert: the SecurityIssue ontology label and its normalized fields.
    assert check_nodes(
        neo4j_session,
        "SecurityIssue",
        [
            "id",
            "_ont_title",
            "_ont_severity",
            "_ont_type",
            "_ont_status",
            "_ont_source",
        ],
    ) == {
        (
            FINDING_BUCKET_PUBLIC_ID,
            "Ensure S3 buckets are not publicly accessible",
            "critical",
            "s3",
            "open",
            "prowler",
        ),
        (
            FINDING_BUCKET_ENCRYPTED_ID,
            "Ensure S3 buckets have default encryption enabled",
            "info",
            "s3",
            "ignored",
            "prowler",
        ),
        (
            FINDING_IAM_USER_ID,
            "Ensure IAM users have MFA enabled",
            "medium",
            "iam",
            "fixed",
            "prowler",
        ),
    }

    # Assert: relationships.
    assert check_rels(
        neo4j_session,
        "ProwlerTenant",
        "id",
        "ProwlerProvider",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, PROVIDER_AWS_ID),
        (TENANT_ID, PROVIDER_KUBERNETES_ID),
        (TENANT_ID, PROVIDER_GITHUB_ID),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerTenant",
        "id",
        "ProwlerScan",
        "id",
        "RESOURCE",
    ) == {(TENANT_ID, SCAN_AWS_ID), (TENANT_ID, SCAN_GITHUB_ID)}
    assert check_rels(
        neo4j_session,
        "ProwlerTenant",
        "id",
        "ProwlerResource",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, RESOURCE_BUCKET_ID),
        (TENANT_ID, RESOURCE_INSTANCE_ID),
        (TENANT_ID, RESOURCE_IAM_USER_ID),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerTenant",
        "id",
        "ProwlerFinding",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, FINDING_BUCKET_PUBLIC_ID),
        (TENANT_ID, FINDING_BUCKET_ENCRYPTED_ID),
        (TENANT_ID, FINDING_IAM_USER_ID),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerProvider",
        "id",
        "ProwlerResource",
        "id",
        "RESOURCE",
    ) == {
        (PROVIDER_AWS_ID, RESOURCE_BUCKET_ID),
        (PROVIDER_AWS_ID, RESOURCE_INSTANCE_ID),
        (PROVIDER_AWS_ID, RESOURCE_IAM_USER_ID),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerScan",
        "id",
        "ProwlerProvider",
        "id",
        "SCANNED",
    ) == {
        (SCAN_AWS_ID, PROVIDER_AWS_ID),
        (SCAN_GITHUB_ID, PROVIDER_GITHUB_ID),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerScan",
        "id",
        "ProwlerFinding",
        "id",
        "IDENTIFIED",
    ) == {
        (SCAN_AWS_ID, FINDING_BUCKET_PUBLIC_ID),
        (SCAN_AWS_ID, FINDING_BUCKET_ENCRYPTED_ID),
        (SCAN_AWS_ID, FINDING_IAM_USER_ID),
    }
    # One finding names two resources, so AFFECTS fans out to both.
    assert check_rels(
        neo4j_session,
        "ProwlerFinding",
        "id",
        "ProwlerResource",
        "id",
        "AFFECTS",
    ) == {
        (FINDING_BUCKET_PUBLIC_ID, RESOURCE_BUCKET_ID),
        (FINDING_BUCKET_PUBLIC_ID, RESOURCE_INSTANCE_ID),
        (FINDING_BUCKET_ENCRYPTED_ID, RESOURCE_BUCKET_ID),
        (FINDING_IAM_USER_ID, RESOURCE_IAM_USER_ID),
    }
    assert _sync_metadata_lastupdated(neo4j_session) == TEST_UPDATE_TAG


def test_providers_link_to_existing_cloud_accounts(neo4j_session, mocker):
    # Arrange
    _patch_prowler_api(mocker)
    _seed_aws_account(neo4j_session)
    _seed_kubernetes_cluster(neo4j_session)

    # Act
    cartography.intel.prowler.start_prowler_ingestion(neo4j_session, _config())

    # Assert
    assert check_rels(
        neo4j_session,
        "ProwlerProvider",
        "id",
        "AWSAccount",
        "id",
        "SCANS",
    ) == {(PROVIDER_AWS_ID, AWS_ACCOUNT_ID)}
    assert check_rels(
        neo4j_session,
        "ProwlerProvider",
        "id",
        "KubernetesCluster",
        "name",
        "SCANS",
    ) == {(PROVIDER_KUBERNETES_ID, KUBERNETES_CLUSTER_NAME)}
    # The GitHub provider is not a cloud tenant type, so it gets no SCANS edge.
    scanning_providers = neo4j_session.run(
        """
        MATCH (p:ProwlerProvider)-[:SCANS]->()
        RETURN collect(DISTINCT p.id) AS provider_ids
        """,
    ).single()["provider_ids"]
    assert sorted(scanning_providers) == sorted(
        [PROVIDER_AWS_ID, PROVIDER_KUBERNETES_ID],
    )


def test_findings_are_paginated_across_multiple_pages(neo4j_session, mocker):
    # Arrange
    fake = _patch_prowler_api(mocker)
    fake.page_sizes["findings"] = 1
    fake.page_sizes["resources"] = 2

    # Act
    cartography.intel.prowler.start_prowler_ingestion(neo4j_session, _config())

    # Assert
    findings_pages = [
        page for collection, page in fake.requested_pages if collection == "findings"
    ]
    assert findings_pages == [1, 2, 3]
    resources_pages = [
        page for collection, page in fake.requested_pages if collection == "resources"
    ]
    assert resources_pages == [1, 2]
    assert check_nodes(neo4j_session, "ProwlerFinding", ["id"]) == {
        (FINDING_BUCKET_PUBLIC_ID,),
        (FINDING_BUCKET_ENCRYPTED_ID,),
        (FINDING_IAM_USER_ID,),
    }
    assert check_nodes(neo4j_session, "ProwlerResource", ["id"]) == {
        (RESOURCE_BUCKET_ID,),
        (RESOURCE_INSTANCE_ID,),
        (RESOURCE_IAM_USER_ID,),
    }
    # `included` is per-document, so the two-resource finding still resolves both
    # ARNs even though its resources arrived on their own findings page.
    assert sorted(
        _list_property(
            neo4j_session,
            "ProwlerFinding",
            FINDING_BUCKET_PUBLIC_ID,
            "resource_uids",
        ),
    ) == sorted([RESOURCE_BUCKET_UID, RESOURCE_INSTANCE_UID])
    assert check_rels(
        neo4j_session,
        "ProwlerFinding",
        "id",
        "ProwlerResource",
        "id",
        "AFFECTS",
    ) == {
        (FINDING_BUCKET_PUBLIC_ID, RESOURCE_BUCKET_ID),
        (FINDING_BUCKET_PUBLIC_ID, RESOURCE_INSTANCE_ID),
        (FINDING_BUCKET_ENCRYPTED_ID, RESOURCE_BUCKET_ID),
        (FINDING_IAM_USER_ID, RESOURCE_IAM_USER_ID),
    }


def test_second_sync_cleans_up_stale_findings_and_resources(neo4j_session, mocker):
    # Arrange
    fake = _patch_prowler_api(mocker)
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    fake.remove("findings", FINDING_IAM_USER_ID)
    fake.remove("resources", RESOURCE_IAM_USER_ID)

    # Act
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(neo4j_session, "ProwlerFinding", ["id"]) == {
        (FINDING_BUCKET_PUBLIC_ID,),
        (FINDING_BUCKET_ENCRYPTED_ID,),
    }
    assert check_nodes(neo4j_session, "ProwlerResource", ["id"]) == {
        (RESOURCE_BUCKET_ID,),
        (RESOURCE_INSTANCE_ID,),
    }
    assert check_nodes(neo4j_session, "ProwlerScan", ["id"]) == {
        (SCAN_AWS_ID,),
        (SCAN_GITHUB_ID,),
    }
    assert check_nodes(neo4j_session, "ProwlerProvider", ["id"]) == {
        (PROVIDER_AWS_ID,),
        (PROVIDER_KUBERNETES_ID,),
        (PROVIDER_GITHUB_ID,),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerTenant",
        "id",
        "ProwlerFinding",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, FINDING_BUCKET_PUBLIC_ID),
        (TENANT_ID, FINDING_BUCKET_ENCRYPTED_ID),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerFinding",
        "id",
        "ProwlerResource",
        "id",
        "AFFECTS",
    ) == {
        (FINDING_BUCKET_PUBLIC_ID, RESOURCE_BUCKET_ID),
        (FINDING_BUCKET_PUBLIC_ID, RESOURCE_INSTANCE_ID),
        (FINDING_BUCKET_ENCRYPTED_ID, RESOURCE_BUCKET_ID),
    }
    assert _sync_metadata_lastupdated(neo4j_session) == TEST_UPDATE_TAG + 1


def test_failed_second_sync_preserves_last_known_good_graph(neo4j_session, mocker):
    # Arrange
    fake = _patch_prowler_api(mocker)
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    original_findings = check_nodes(neo4j_session, "ProwlerFinding", ["id", "status"])
    original_resources = check_nodes(neo4j_session, "ProwlerResource", ["id", "uid"])
    original_providers = check_nodes(neo4j_session, "ProwlerProvider", ["id", "uid"])
    original_scans = check_nodes(neo4j_session, "ProwlerScan", ["id", "state"])
    original_affects = check_rels(
        neo4j_session,
        "ProwlerFinding",
        "id",
        "ProwlerResource",
        "id",
        "AFFECTS",
    )
    original_tenant_rels = check_rels(
        neo4j_session,
        "ProwlerTenant",
        "id",
        "ProwlerFinding",
        "id",
        "RESOURCE",
    )

    # The second sync would have dropped these, had it completed.
    fake.remove("findings", FINDING_IAM_USER_ID)
    fake.remove("resources", RESOURCE_IAM_USER_ID)
    fake.page_sizes["findings"] = 1
    fake.fail_on = ("findings", 2)

    # Act and assert
    with pytest.raises(RuntimeError, match="synthetic Prowler findings page 2 failure"):
        cartography.intel.prowler.start_prowler_ingestion(
            neo4j_session,
            _config(TEST_UPDATE_TAG + 1),
        )

    # Assert: cleanup is deferred until every feed lands, so nothing was deleted.
    assert (
        check_nodes(neo4j_session, "ProwlerFinding", ["id", "status"])
        == original_findings
    )
    assert (
        check_nodes(neo4j_session, "ProwlerResource", ["id", "uid"])
        == original_resources
    )
    assert (
        check_nodes(neo4j_session, "ProwlerProvider", ["id", "uid"])
        == original_providers
    )
    assert check_nodes(neo4j_session, "ProwlerScan", ["id", "state"]) == original_scans
    assert (
        check_rels(
            neo4j_session,
            "ProwlerFinding",
            "id",
            "ProwlerResource",
            "id",
            "AFFECTS",
        )
        == original_affects
    )
    assert (
        check_rels(
            neo4j_session,
            "ProwlerTenant",
            "id",
            "ProwlerFinding",
            "id",
            "RESOURCE",
        )
        == original_tenant_rels
    )
    assert _sync_metadata_lastupdated(neo4j_session) == TEST_UPDATE_TAG


def test_identical_sync_is_idempotent_with_exact_counts(neo4j_session, mocker):
    # Arrange
    _patch_prowler_api(mocker)
    _seed_aws_account(neo4j_session)

    # Act
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    first_counts = {
        label: _node_count(neo4j_session, label) for label in PROWLER_LABELS
    }
    first_rel_counts = {
        rel: _rel_count(neo4j_session, rel)
        for rel in ("RESOURCE", "SCANNED", "IDENTIFIED", "AFFECTS", "SCANS")
    }
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert first_counts == {
        "ProwlerTenant": 1,
        "ProwlerProvider": 3,
        "ProwlerScan": 2,
        "ProwlerResource": 3,
        "ProwlerFinding": 3,
    }
    assert first_rel_counts == {
        "RESOURCE": 14,
        "SCANNED": 2,
        "IDENTIFIED": 3,
        "AFFECTS": 4,
        "SCANS": 1,
    }
    assert {
        label: _node_count(neo4j_session, label) for label in PROWLER_LABELS
    } == first_counts
    assert {
        rel: _rel_count(neo4j_session, rel)
        for rel in ("RESOURCE", "SCANNED", "IDENTIFIED", "AFFECTS", "SCANS")
    } == first_rel_counts
    metadata_count = neo4j_session.run(
        "MATCH (n:ModuleSyncMetadata {id: $id}) RETURN count(n) AS count",
        id=SYNC_METADATA_ID,
    ).single()["count"]
    assert metadata_count == 1
