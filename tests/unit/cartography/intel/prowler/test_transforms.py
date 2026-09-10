import pytest

from cartography.intel.prowler import findings
from cartography.intel.prowler import providers
from cartography.intel.prowler import resources
from cartography.intel.prowler import scans
from cartography.models.ontology.mapping.data.security_issues import _PROWLER_SEVERITY
from cartography.models.ontology.mapping.data.security_issues import _PROWLER_STATUS

# Enum values published by the Prowler API v1 OpenAPI schema. The ontology maps
# must stay exhaustive against these, or a finding silently loses its normalized
# severity or status.
API_SEVERITIES = ("critical", "high", "informational", "low", "medium")
API_TRIAGE_STATUSES = (
    "false_positive",
    "open",
    "remediating",
    "reopened",
    "resolved",
    "risk_accepted",
    "under_review",
)
API_PROVIDER_TYPES = (
    "alibabacloud",
    "aws",
    "azure",
    "cloudflare",
    "gcp",
    "github",
    "googleworkspace",
    "iac",
    "image",
    "kubernetes",
    "m365",
    "mongodbatlas",
    "okta",
    "openstack",
    "oraclecloud",
    "vercel",
)


def test_severity_map_covers_every_api_severity() -> None:
    assert set(_PROWLER_SEVERITY) == set(API_SEVERITIES)


def test_triage_status_map_covers_every_api_status() -> None:
    assert set(_PROWLER_STATUS) == set(API_TRIAGE_STATUSES)


@pytest.mark.parametrize("provider_type", API_PROVIDER_TYPES)  # type: ignore[misc]
def test_every_provider_type_transforms(provider_type: str) -> None:
    """An unrecognized provider type must still ingest, just without a cloud link."""
    # Arrange
    raw = [
        {
            "type": "providers",
            "id": "p1",
            "attributes": {"provider": provider_type, "uid": "some-uid"},
        },
    ]

    # Act
    transformed = providers.transform(raw)

    # Assert
    assert len(transformed) == 1
    row = transformed[0]
    assert row["provider_type"] == provider_type
    # Exactly one cloud field is set for the four linkable types, none otherwise.
    cloud_fields = [
        row["aws_account_id"],
        row["azure_subscription_id"],
        row["gcp_project_id"],
        row["kubernetes_cluster_name"],
    ]
    populated = [value for value in cloud_fields if value is not None]
    if provider_type in ("aws", "azure", "gcp", "kubernetes"):
        assert populated == ["some-uid"]
    else:
        assert populated == []


def test_provider_transform_reads_the_connection_object() -> None:
    # Arrange
    raw = [
        {
            "id": "p1",
            "attributes": {
                "provider": "aws",
                "uid": "111122223333",
                "connection": {
                    "connected": True,
                    "last_checked_at": "2026-09-09T02:59:58.770914Z",
                },
            },
        },
    ]

    # Act
    row = providers.transform(raw)[0]

    # Assert
    assert row["connected"] is True
    assert row["connection_last_checked_at"] is not None
    assert row["connection_last_checked_at"].tzinfo is not None


def test_provider_transform_tolerates_a_missing_connection() -> None:
    raw = [{"id": "p1", "attributes": {"provider": "aws", "uid": "111122223333"}}]
    row = providers.transform(raw)[0]
    assert row["connected"] is None
    assert row["connection_last_checked_at"] is None


def test_scan_transform_reads_the_provider_relationship() -> None:
    # Arrange
    raw = [
        {
            "id": "s1",
            "attributes": {"state": "completed", "progress": 100},
            "relationships": {"provider": {"data": {"type": "providers", "id": "p1"}}},
        },
    ]

    # Act
    row = scans.transform(raw)[0]

    # Assert
    assert row["provider_id"] == "p1"
    assert row["state"] == "completed"


def test_scan_transform_tolerates_a_null_relationship() -> None:
    # Prowler renders an absent to-one relationship as {"data": null}.
    raw = [
        {
            "id": "s1",
            "attributes": {},
            "relationships": {"provider": {"data": None}},
        },
    ]
    assert scans.transform(raw)[0]["provider_id"] is None


def test_resource_transform_flattens_tags() -> None:
    # Arrange: Neo4j cannot store a nested map, so tags become two sorted lists.
    raw = [
        {
            "id": "r1",
            "attributes": {
                "uid": "arn:aws:s3:::bucket",
                "name": "bucket",
                "region": "us-east-1",
                "service": "s3",
                "type": "AwsS3Bucket",
                "tags": {"owner": "platform", "env": "prod"},
            },
        },
    ]

    # Act
    row = resources.transform(raw)[0]

    # Assert
    assert row["tag_keys"] == ["env", "owner"]
    assert row["tags"] == ["env=prod", "owner=platform"]
    assert row["resource_type"] == "AwsS3Bucket"


def test_resource_transform_treats_empty_tags_as_absent() -> None:
    raw = [
        {
            "id": "r1",
            "attributes": {
                "uid": "arn:aws:s3:::bucket",
                "name": "b",
                "region": "us-east-1",
                "service": "s3",
                "tags": {},
            },
        },
    ]
    row = resources.transform(raw)[0]
    assert row["tag_keys"] is None
    assert row["tags"] is None


def _finding_page(attributes: dict, relationships: dict | None = None) -> list[dict]:
    return [
        {
            "findings": [
                {
                    "id": "f1",
                    "attributes": {
                        "uid": "prowler-aws-check-1-111122223333-us-east-1-bucket",
                        "check_id": "check_1",
                        "severity": "critical",
                        **attributes,
                    },
                    "relationships": relationships or {},
                },
            ],
            "resources": {},
        },
    ]


def test_finding_transform_reads_lowercase_check_metadata() -> None:
    """The API lowercases every check-metadata key, including nested ones."""
    # Arrange
    page = _finding_page(
        {
            "status": "FAIL",
            "check_metadata": {
                "checktitle": "Check S3 Bucket Public Access Block",
                "servicename": "s3",
                "resourcetype": "AwsS3Bucket",
                "risk": "Public buckets expose data.",
                "compliance": {"SOC2": ["cc6.1"], "CIS-2.0": ["2.1.5"]},
                "remediation": {
                    "code": {
                        "cli": "aws s3api put-public-access-block",
                        "terraform": "tf",
                    },
                    "recommendation": {"text": "Enable it.", "url": "https://example"},
                },
            },
        },
    )

    # Act
    row = findings.transform(page)[0]

    # Assert
    assert row["check_title"] == "Check S3 Bucket Public Access Block"
    assert row["service_name"] == "s3"
    assert row["resource_type"] == "AwsS3Bucket"
    assert row["remediation_text"] == "Enable it."
    assert row["remediation_url"] == "https://example"
    assert row["remediation_cli"] == "aws s3api put-public-access-block"
    assert row["remediation_terraform"] == "tf"
    assert row["compliance_frameworks"] == ["CIS-2.0", "SOC2"]


def test_finding_transform_tolerates_missing_check_metadata() -> None:
    # check_metadata is not a required attribute of a finding.
    row = findings.transform(_finding_page({"status": "PASS"}))[0]
    assert row["check_title"] is None
    assert row["compliance_frameworks"] is None
    assert row["cve_ids"] is None


def test_finding_transform_extracts_only_canonical_cve_ids() -> None:
    # Arrange
    page = _finding_page(
        {
            "check_metadata": {
                "relatedto": ["CVE-2026-12345", "GHSA-not-a-cve", "cve-2026-9999"],
                "checkaliases": ["some_alias"],
            },
        },
    )

    # Act
    row = findings.transform(page)[0]

    # Assert: uppercased, deduped, non-CVE strings dropped.
    assert row["cve_ids"] == ["CVE-2026-12345", "CVE-2026-9999"]


def test_finding_transform_links_multiple_resources() -> None:
    # Arrange
    page = [
        {
            "findings": [
                {
                    "id": "f1",
                    "attributes": {
                        "uid": "u1",
                        "check_id": "c1",
                        "severity": "high",
                    },
                    "relationships": {
                        "resources": {
                            "data": [
                                {"type": "resources", "id": "r1"},
                                {"type": "resources", "id": "r2"},
                            ],
                        },
                    },
                },
            ],
            "resources": {
                "r1": {"id": "r1", "attributes": {"uid": "arn:aws:s3:::one"}},
                # r2 is deliberately not sideloaded on this page.
            },
        },
    ]

    # Act
    row = findings.transform(page)[0]

    # Assert: both ids link; only the sideloaded ARN is resolvable.
    assert row["resource_ids"] == ["r1", "r2"]
    assert row["resource_uids"] == ["arn:aws:s3:::one"]


@pytest.mark.parametrize("missing", ["uid", "check_id", "severity"])  # type: ignore[misc]
def test_finding_transform_requires_the_api_required_attributes(missing: str) -> None:
    page = _finding_page({})
    del page[0]["findings"][0]["attributes"][missing]
    with pytest.raises(ValueError):
        findings.transform(page)
