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
from tests.data.prowler import COMPLIANCE_AWS_CIS_ID
from tests.data.prowler import COMPLIANCE_AWS_CIS_NODE_ID
from tests.data.prowler import COMPLIANCE_AWS_SOC2_ID
from tests.data.prowler import COMPLIANCE_AWS_SOC2_NODE_ID
from tests.data.prowler import COMPLIANCE_AWS_SOC2_OBJECT_ID
from tests.data.prowler import COMPLIANCE_K8S_CIS_ID
from tests.data.prowler import COMPLIANCE_K8S_CIS_NODE_ID
from tests.data.prowler import COMPLIANCE_OVERVIEWS_BY_PROVIDER
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
from tests.data.prowler import RESOURCE_K8S_POD_ID
from tests.data.prowler import RESOURCE_K8S_POD_UID
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
    "/api/v1/compliance-overviews": "compliance-overviews",
}
DEFAULT_PAGE_SIZE = 100

# Every relationship label the module writes from a Prowler node.
_COUNTED_RELS = (
    "RESOURCE",
    "CONTAINS",
    "SCANNED",
    "IDENTIFIED",
    "AFFECTS",
    "SCANS",
    "ASSESSES",
    "REPRESENTS",
)

PROWLER_LABELS = (
    "ProwlerTenant",
    "ProwlerProvider",
    "ProwlerScan",
    "ProwlerResource",
    "ProwlerFinding",
    "ProwlerComplianceAssessment",
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
        # Compliance overviews are not one flat collection: the API serves them
        # per provider, selected by a `filter[provider_id]` query parameter.
        self.compliance_by_provider: dict[str, list[dict[str, Any]]] = {
            provider_id: deepcopy(overviews)
            for provider_id, overviews in COMPLIANCE_OVERVIEWS_BY_PROVIDER.items()
        }
        self.page_sizes: dict[str, int] = {}
        self.fail_on: tuple[str, int] | None = None
        self.requested_pages: list[tuple[str, int]] = []
        self.compliance_provider_requests: list[str] = []

    def remove(self, collection: str, object_id: str) -> None:
        """Drop one object from the fake's state, as Prowler would on deletion."""
        rows = self.state[collection]
        remaining = [row for row in rows if row["id"] != object_id]
        assert len(remaining) == len(rows) - 1, f"{object_id} not in {collection}"
        self.state[collection] = remaining

    def remove_compliance(self, provider_id: str, object_id: str) -> None:
        """Drop one compliance overview from one provider's collection."""
        rows = self.compliance_by_provider[provider_id]
        remaining = [row for row in rows if row["id"] != object_id]
        assert (
            len(remaining) == len(rows) - 1
        ), f"{object_id} not in {provider_id} compliance overviews"
        self.compliance_by_provider[provider_id] = remaining

    def set_finding_status(self, finding_id: str, status: str) -> None:
        """Change one finding's status, as a later scan would."""
        for finding in self.state["findings"]:
            if finding["id"] == finding_id:
                finding["attributes"]["status"] = status
                return
        raise AssertionError(f"{finding_id} not in findings")

    def _sideloaded_providers(
        self,
        resources: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        wanted: list[str] = []
        for resource in resources:
            provider_id = resource["relationships"]["provider"]["data"]["id"]
            if provider_id not in wanted:
                wanted.append(provider_id)
        by_id = {provider["id"]: provider for provider in self.state["providers"]}
        return [deepcopy(by_id[uuid]) for uuid in wanted if uuid in by_id]

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
        if collection == "resources":
            assert query.get("include") == "provider"

        page_number = int(query.get("page[number]", 1))
        self.requested_pages.append((collection, page_number))
        if self.fail_on == (collection, page_number):
            raise RuntimeError(
                f"synthetic Prowler {collection} page {page_number} failure",
            )

        if collection == "compliance-overviews":
            # The module must scope every compliance request to one provider;
            # an unfiltered request would report against an arbitrary scan.
            provider_id = query.get("filter[provider_id]")
            assert provider_id, "compliance overviews must be filtered by provider"
            if page_number == 1:
                self.compliance_provider_requests.append(provider_id)
            assert (
                provider_id in self.compliance_by_provider
            ), f"Unexpected Prowler provider filter {provider_id}"
            rows = self.compliance_by_provider[provider_id]
        else:
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
        if collection == "resources":
            document["included"] = self._sideloaded_providers(page_rows)
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
            """
            MATCH (n)
            WHERE (n:AWSS3Bucket OR n:AWSEC2Instance) AND n.arn IN $arns
            DETACH DELETE n
            """,
            arns=[RESOURCE_BUCKET_UID, RESOURCE_INSTANCE_UID],
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


def _seed_aws_resources(neo4j_session) -> None:
    """Seed the AWS nodes whose ARNs match the Prowler resource uids.

    Only the indexed `arn` matters to the REPRESENTS matchers, but these are
    written the way the AWS modules write them, with `id` set too.
    """
    neo4j_session.run(
        """
        MERGE (b:AWSS3Bucket {id: $bucket_name})
        SET b.arn = $bucket_arn,
            b.name = $bucket_name,
            b.lastupdated = $update_tag
        MERGE (i:AWSEC2Instance {id: $instance_id})
        SET i.arn = $instance_arn,
            i.instanceid = $instance_id,
            i.lastupdated = $update_tag
        """,
        bucket_arn=RESOURCE_BUCKET_UID,
        bucket_name="synthetic-prowler-bucket",
        instance_arn=RESOURCE_INSTANCE_UID,
        instance_id="i-00000000000000001",
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


def _labels(neo4j_session, label: str, node_id: str) -> list[str]:
    """Return every label on one node, to check conditional extra labels."""
    record = neo4j_session.run(
        f"MATCH (n:{label} {{id: $node_id}}) RETURN labels(n) AS labels",
        node_id=node_id,
    ).single()
    assert record is not None, f"{label} {node_id} not found"
    return record["labels"]


def _node_count(neo4j_session, label: str) -> int:
    return neo4j_session.run(
        f"MATCH (n:{label}) RETURN count(n) AS count",
    ).single()["count"]


def _rel_count(neo4j_session, rel_label: str) -> int:
    return neo4j_session.run(
        f"""
        MATCH (n1)-[r:{rel_label}]->(n2)
        WHERE (n1:ProwlerTenant OR n1:ProwlerProvider OR n1:ProwlerScan
               OR n1:ProwlerResource OR n1:ProwlerFinding
               OR n1:ProwlerComplianceAssessment)
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

    # Assert: resources. `aws_uid` is only populated for an AWS ARN, because it
    # is the matcher the REPRESENTS correlation edges join on.
    assert check_nodes(
        neo4j_session,
        "ProwlerResource",
        [
            "id",
            "uid",
            "aws_uid",
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
            RESOURCE_IAM_USER_UID,
            "synthetic-user",
            "us-east-1",
            "iam",
            "AwsIamUser",
            "aws",
            1,
            PROVIDER_AWS_ID,
        ),
        (
            RESOURCE_K8S_POD_ID,
            RESOURCE_K8S_POD_UID,
            # Not an AWS provider, so there is nothing to correlate on.
            None,
            "synthetic-api-7f9c",
            "default",
            "core",
            "Pod",
            None,
            0,
            PROVIDER_KUBERNETES_ID,
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

    # Assert: compliance assessments, one per (provider, framework) pair.
    assert check_nodes(
        neo4j_session,
        "ProwlerComplianceAssessment",
        [
            "id",
            "compliance_id",
            "framework",
            "version",
            "requirements_passed",
            "requirements_failed",
            "requirements_manual",
            "total_requirements",
            "provider_id",
        ],
    ) == {
        (
            COMPLIANCE_AWS_CIS_NODE_ID,
            COMPLIANCE_AWS_CIS_ID,
            "CIS",
            "2.0",
            42,
            7,
            3,
            52,
            PROVIDER_AWS_ID,
        ),
        (
            COMPLIANCE_AWS_SOC2_NODE_ID,
            COMPLIANCE_AWS_SOC2_ID,
            "SOC2",
            # The API reports SOC 2 with an empty version, which normalizes away.
            None,
            25,
            12,
            5,
            42,
            PROVIDER_AWS_ID,
        ),
        (
            COMPLIANCE_K8S_CIS_NODE_ID,
            COMPLIANCE_K8S_CIS_ID,
            "CIS",
            "1.10",
            18,
            4,
            6,
            28,
            PROVIDER_KUBERNETES_ID,
        ),
    }

    # Assert: the SecurityIssue ontology label and its normalized fields. Only
    # the failing checks carry the label; see the dedicated test below.
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
        (TENANT_ID, RESOURCE_K8S_POD_ID),
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
        "CONTAINS",
    ) == {
        (PROVIDER_AWS_ID, RESOURCE_BUCKET_ID),
        (PROVIDER_AWS_ID, RESOURCE_INSTANCE_ID),
        (PROVIDER_AWS_ID, RESOURCE_IAM_USER_ID),
        (PROVIDER_KUBERNETES_ID, RESOURCE_K8S_POD_ID),
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
    assert check_rels(
        neo4j_session,
        "ProwlerTenant",
        "id",
        "ProwlerComplianceAssessment",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, COMPLIANCE_AWS_CIS_NODE_ID),
        (TENANT_ID, COMPLIANCE_AWS_SOC2_NODE_ID),
        (TENANT_ID, COMPLIANCE_K8S_CIS_NODE_ID),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerComplianceAssessment",
        "id",
        "ProwlerProvider",
        "id",
        "ASSESSES",
    ) == {
        (COMPLIANCE_AWS_CIS_NODE_ID, PROVIDER_AWS_ID),
        (COMPLIANCE_AWS_SOC2_NODE_ID, PROVIDER_AWS_ID),
        (COMPLIANCE_K8S_CIS_NODE_ID, PROVIDER_KUBERNETES_ID),
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


def test_resources_represent_correlated_aws_nodes(neo4j_session, mocker):
    # Arrange
    _patch_prowler_api(mocker)
    _seed_aws_resources(neo4j_session)

    # Act
    cartography.intel.prowler.start_prowler_ingestion(neo4j_session, _config())

    # Assert: each AWS resource whose uid is an ARN is joined to the cloud node
    # carrying that ARN.
    assert check_rels(
        neo4j_session,
        "ProwlerResource",
        "id",
        "AWSS3Bucket",
        "arn",
        "REPRESENTS",
    ) == {(RESOURCE_BUCKET_ID, RESOURCE_BUCKET_UID)}
    assert check_rels(
        neo4j_session,
        "ProwlerResource",
        "id",
        "AWSEC2Instance",
        "arn",
        "REPRESENTS",
    ) == {(RESOURCE_INSTANCE_ID, RESOURCE_INSTANCE_UID)}

    # Assert: the whole point of the correlation is that a finding on an AWS
    # resource is now reachable from the AWS node itself.
    findings_on_bucket = neo4j_session.run(
        """
        MATCH (b:AWSS3Bucket {arn: $bucket_arn})
              <-[:REPRESENTS]-(:ProwlerResource)
              <-[:AFFECTS]-(f:ProwlerFinding)
        RETURN collect(DISTINCT f.id) AS finding_ids
        """,
        bucket_arn=RESOURCE_BUCKET_UID,
    ).single()["finding_ids"]
    assert sorted(findings_on_bucket) == sorted(
        [FINDING_BUCKET_PUBLIC_ID, FINDING_BUCKET_ENCRYPTED_ID],
    )

    # Assert: only the two seeded ARNs correlate. The IAM user's ARN has no node
    # in the graph, and the Kubernetes resource belongs to a provider whose uids
    # are not ARNs at all, so its matcher value is null and never matches.
    represented = neo4j_session.run(
        """
        MATCH (r:ProwlerResource)-[:REPRESENTS]->()
        RETURN collect(DISTINCT r.id) AS resource_ids
        """,
    ).single()["resource_ids"]
    assert sorted(represented) == sorted([RESOURCE_BUCKET_ID, RESOURCE_INSTANCE_ID])
    assert RESOURCE_K8S_POD_ID not in represented


def test_only_failing_findings_are_security_issues(neo4j_session, mocker):
    # Arrange
    fake = _patch_prowler_api(mocker)

    # Act
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )

    # Assert: the two FAIL findings carry the label, the PASS one does not.
    assert check_nodes(neo4j_session, "SecurityIssue", ["id", "status"]) == {
        (FINDING_BUCKET_PUBLIC_ID, "FAIL"),
        (FINDING_IAM_USER_ID, "FAIL"),
    }
    assert "SecurityIssue" not in _labels(
        neo4j_session,
        "ProwlerFinding",
        FINDING_BUCKET_ENCRYPTED_ID,
    )
    # Every finding, passing ones included, still gets its normalized ontology
    # fields. The label is what marks a finding as an open security issue.
    assert check_nodes(
        neo4j_session,
        "ProwlerFinding",
        ["id", "_ont_title", "_ont_severity", "_ont_status"],
    ) == {
        (
            FINDING_BUCKET_PUBLIC_ID,
            "Ensure S3 buckets are not publicly accessible",
            "critical",
            "open",
        ),
        (
            FINDING_BUCKET_ENCRYPTED_ID,
            "Ensure S3 buckets have default encryption enabled",
            "info",
            "ignored",
        ),
        (
            FINDING_IAM_USER_ID,
            "Ensure IAM users have MFA enabled",
            "medium",
            "fixed",
        ),
    }

    # Act: the next scan finds the bucket remediated.
    fake.set_finding_status(FINDING_BUCKET_PUBLIC_ID, "PASS")
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert: the label is removed again, not left behind by the earlier sync.
    assert check_nodes(neo4j_session, "SecurityIssue", ["id"]) == {
        (FINDING_IAM_USER_ID,),
    }
    assert "SecurityIssue" not in _labels(
        neo4j_session,
        "ProwlerFinding",
        FINDING_BUCKET_PUBLIC_ID,
    )


def test_compliance_assessments_are_fetched_per_provider_and_cleaned_up(
    neo4j_session,
    mocker,
):
    # Arrange
    fake = _patch_prowler_api(mocker)
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    # One request per provider, each scoped to that provider's latest scan.
    assert fake.compliance_provider_requests == [
        PROVIDER_AWS_ID,
        PROVIDER_KUBERNETES_ID,
        PROVIDER_GITHUB_ID,
    ]
    assert check_nodes(neo4j_session, "ProwlerComplianceAssessment", ["id"]) == {
        (COMPLIANCE_AWS_CIS_NODE_ID,),
        (COMPLIANCE_AWS_SOC2_NODE_ID,),
        (COMPLIANCE_K8S_CIS_NODE_ID,),
    }

    # Act: the provider stops being assessed against SOC 2.
    fake.remove_compliance(PROVIDER_AWS_ID, COMPLIANCE_AWS_SOC2_OBJECT_ID)
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(neo4j_session, "ProwlerComplianceAssessment", ["id"]) == {
        (COMPLIANCE_AWS_CIS_NODE_ID,),
        (COMPLIANCE_K8S_CIS_NODE_ID,),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerTenant",
        "id",
        "ProwlerComplianceAssessment",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, COMPLIANCE_AWS_CIS_NODE_ID),
        (TENANT_ID, COMPLIANCE_K8S_CIS_NODE_ID),
    }
    assert check_rels(
        neo4j_session,
        "ProwlerComplianceAssessment",
        "id",
        "ProwlerProvider",
        "id",
        "ASSESSES",
    ) == {
        (COMPLIANCE_AWS_CIS_NODE_ID, PROVIDER_AWS_ID),
        (COMPLIANCE_K8S_CIS_NODE_ID, PROVIDER_KUBERNETES_ID),
    }


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
        (RESOURCE_K8S_POD_ID,),
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
        (RESOURCE_K8S_POD_ID,),
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
    original_assessments = check_nodes(
        neo4j_session,
        "ProwlerComplianceAssessment",
        ["id", "requirements_failed"],
    )
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
        check_nodes(
            neo4j_session,
            "ProwlerComplianceAssessment",
            ["id", "requirements_failed"],
        )
        == original_assessments
    )
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
    _seed_aws_resources(neo4j_session)

    # Act
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    first_counts = {
        label: _node_count(neo4j_session, label) for label in PROWLER_LABELS
    }
    first_rel_counts = {rel: _rel_count(neo4j_session, rel) for rel in _COUNTED_RELS}
    cartography.intel.prowler.start_prowler_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert first_counts == {
        "ProwlerTenant": 1,
        "ProwlerProvider": 3,
        "ProwlerScan": 2,
        "ProwlerResource": 4,
        "ProwlerFinding": 3,
        # CIS 2.0 and SOC 2 for the AWS provider, CIS 1.10 for the Kubernetes
        # one. The GitHub provider reports no compliance overviews.
        "ProwlerComplianceAssessment": 3,
    }
    assert first_rel_counts == {
        # 3 providers + 2 scans + 4 resources + 3 findings + 3 compliance
        # assessments, all owned by the tenant.
        "RESOURCE": 15,
        # The AWS provider contains 3 resources, the Kubernetes one contains 1.
        "CONTAINS": 4,
        "SCANNED": 2,
        "IDENTIFIED": 3,
        "AFFECTS": 4,
        "SCANS": 1,
        "ASSESSES": 3,
        # The seeded bucket and instance; the IAM user and the Kubernetes pod
        # have no AWS node to correlate with.
        "REPRESENTS": 2,
    }
    assert {
        label: _node_count(neo4j_session, label) for label in PROWLER_LABELS
    } == first_counts
    assert {
        rel: _rel_count(neo4j_session, rel) for rel in _COUNTED_RELS
    } == first_rel_counts
    metadata_count = neo4j_session.run(
        "MATCH (n:ModuleSyncMetadata {id: $id}) RETURN count(n) AS count",
        id=SYNC_METADATA_ID,
    ).single()["count"]
    assert metadata_count == 1
