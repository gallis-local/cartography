"""Synthetic Prowler API v1 fixtures.

Every object below mirrors the JSON:API shape the real Prowler API returns, so
the module's transforms run against realistic input. All identifiers, hostnames,
and account numbers are synthetic.
"""

from typing import Any

API_URL = "https://api.prowler.example"
API_KEY = "synthetic-prowler-api-key"

TENANT_ID = "11111111-1111-4111-8111-111111111111"
TENANT_NAME = "Example Prowler Tenant"

PROVIDER_AWS_ID = "22222222-2222-4222-8222-222222222222"
PROVIDER_KUBERNETES_ID = "33333333-3333-4333-8333-333333333333"
PROVIDER_GITHUB_ID = "44444444-4444-4444-8444-444444444444"

AWS_ACCOUNT_ID = "111122223333"
KUBERNETES_CLUSTER_NAME = "synthetic-cluster"
GITHUB_ORG_UID = "synthetic-github-org"

SCAN_AWS_ID = "55555555-5555-4555-8555-555555555555"
SCAN_GITHUB_ID = "66666666-6666-4666-8666-666666666666"

RESOURCE_BUCKET_ID = "77777777-7777-4777-8777-777777777777"
RESOURCE_INSTANCE_ID = "88888888-8888-4888-8888-888888888888"
RESOURCE_IAM_USER_ID = "99999999-9999-4999-8999-999999999999"

RESOURCE_BUCKET_UID = "arn:aws:s3:::synthetic-prowler-bucket"
RESOURCE_INSTANCE_UID = (
    "arn:aws:ec2:us-west-2:111122223333:instance/i-00000000000000001"
)
RESOURCE_IAM_USER_UID = "arn:aws:iam::111122223333:user/synthetic-user"

RESOURCE_K8S_POD_ID = "12121212-1212-4121-8121-121212121212"
# A Kubernetes resource uid is a cluster-scoped path, never an ARN, so no AWS
# correlation edge can be built from it.
RESOURCE_K8S_POD_UID = "synthetic-cluster/default/pod/synthetic-api-7f9c"

FINDING_BUCKET_PUBLIC_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
FINDING_BUCKET_ENCRYPTED_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
FINDING_IAM_USER_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"

FINDING_BUCKET_PUBLIC_UID = (
    "prowler-aws-s3_bucket_public_access-111122223333-us-west-2-"
    "synthetic-prowler-bucket"
)
FINDING_BUCKET_ENCRYPTED_UID = (
    "prowler-aws-s3_bucket_default_encryption-111122223333-us-west-2-"
    "synthetic-prowler-bucket"
)
FINDING_IAM_USER_UID = (
    "prowler-aws-iam_user_mfa_enabled-111122223333-us-east-1-synthetic-user"
)

CVE_ID = "CVE-2026-12345"

COMPLIANCE_AWS_CIS_OBJECT_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
COMPLIANCE_AWS_SOC2_OBJECT_ID = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
COMPLIANCE_K8S_CIS_OBJECT_ID = "ffffffff-ffff-4fff-8fff-ffffffffffff"

COMPLIANCE_AWS_CIS_ID = "cis_2.0_aws"
COMPLIANCE_AWS_SOC2_ID = "soc2_aws"
COMPLIANCE_K8S_CIS_ID = "cis_1.10_kubernetes"

# The same framework is assessed once per provider, so the graph node id carries
# the provider id as well as the framework id.
COMPLIANCE_AWS_CIS_NODE_ID = f"{PROVIDER_AWS_ID}:{COMPLIANCE_AWS_CIS_ID}"
COMPLIANCE_AWS_SOC2_NODE_ID = f"{PROVIDER_AWS_ID}:{COMPLIANCE_AWS_SOC2_ID}"
COMPLIANCE_K8S_CIS_NODE_ID = f"{PROVIDER_KUBERNETES_ID}:{COMPLIANCE_K8S_CIS_ID}"


TENANTS: list[dict[str, Any]] = [
    {
        "type": "tenants",
        "id": TENANT_ID,
        # The API's tenant resource exposes only `name`.
        "attributes": {
            "name": TENANT_NAME,
        },
    },
]


PROVIDERS: list[dict[str, Any]] = [
    {
        "type": "providers",
        "id": PROVIDER_AWS_ID,
        "attributes": {
            "provider": "aws",
            "uid": AWS_ACCOUNT_ID,
            "alias": "synthetic-aws-production",
            "available": True,
            "is_dynamic": False,
            "is_imported": False,
            "connection": {
                "connected": True,
                "last_checked_at": "2026-08-13T08:30:00.000000Z",
            },
            "inserted_at": "2026-01-05T09:05:00.000000Z",
            "updated_at": "2026-08-13T08:30:00.000000Z",
        },
    },
    {
        "type": "providers",
        "id": PROVIDER_KUBERNETES_ID,
        "attributes": {
            "provider": "kubernetes",
            "uid": KUBERNETES_CLUSTER_NAME,
            "alias": "synthetic-kubernetes",
            "available": True,
            "is_dynamic": False,
            "is_imported": False,
            "connection": {
                "connected": False,
                "last_checked_at": "2026-08-12T08:30:00.000000Z",
            },
            "inserted_at": "2026-02-05T09:05:00.000000Z",
            "updated_at": "2026-08-12T08:30:00.000000Z",
        },
    },
    {
        # GitHub is not one of the provider types Cartography links to a cloud
        # tenant node, so every cloud-link field must stay null for this one.
        "type": "providers",
        "id": PROVIDER_GITHUB_ID,
        "attributes": {
            "provider": "github",
            "uid": GITHUB_ORG_UID,
            "alias": None,
            "available": True,
            "is_dynamic": True,
            "is_imported": False,
            "connection": {
                "connected": True,
                "last_checked_at": "2026-08-13T08:31:00.000000Z",
            },
            "inserted_at": "2026-03-05T09:05:00.000000Z",
            "updated_at": "2026-08-13T08:31:00.000000Z",
        },
    },
]


SCANS: list[dict[str, Any]] = [
    {
        "type": "scans",
        "id": SCAN_AWS_ID,
        "attributes": {
            "name": "synthetic-aws-daily",
            "trigger": "scheduled",
            "state": "completed",
            "unique_resource_count": 3,
            "progress": 100,
            "duration": 412,
            "inserted_at": "2026-08-13T06:00:00.000000Z",
            "started_at": "2026-08-13T06:00:05.000000Z",
            "completed_at": "2026-08-13T06:06:57.000000Z",
            "scheduled_at": "2026-08-13T06:00:00.000000Z",
            "next_scan_at": "2026-08-14T06:00:00.000000Z",
        },
        "relationships": {
            "provider": {"data": {"type": "providers", "id": PROVIDER_AWS_ID}},
        },
    },
    {
        "type": "scans",
        "id": SCAN_GITHUB_ID,
        "attributes": {
            "name": "synthetic-github-manual",
            "trigger": "manual",
            "state": "executing",
            "unique_resource_count": 0,
            "progress": 35,
            "duration": None,
            "inserted_at": "2026-08-13T07:00:00.000000Z",
            "started_at": "2026-08-13T07:00:02.000000Z",
            "completed_at": None,
            "scheduled_at": None,
            "next_scan_at": None,
        },
        "relationships": {
            "provider": {"data": {"type": "providers", "id": PROVIDER_GITHUB_ID}},
        },
    },
]


RESOURCES: list[dict[str, Any]] = [
    {
        "type": "resources",
        "id": RESOURCE_BUCKET_ID,
        "attributes": {
            "uid": RESOURCE_BUCKET_UID,
            "name": "synthetic-prowler-bucket",
            "region": "us-west-2",
            "service": "s3",
            "type": "AwsS3Bucket",
            "tags": {"env": "prod", "owner": "security"},
            "partition": "aws",
            "groups": ["storage"],
            "failed_findings_count": 1,
            "inserted_at": "2026-06-01T00:00:00.000000Z",
            "updated_at": "2026-08-13T06:06:00.000000Z",
        },
        "relationships": {
            "provider": {"data": {"type": "providers", "id": PROVIDER_AWS_ID}},
        },
    },
    {
        "type": "resources",
        "id": RESOURCE_INSTANCE_ID,
        "attributes": {
            "uid": RESOURCE_INSTANCE_UID,
            "name": "synthetic-app-server",
            "region": "us-west-2",
            "service": "ec2",
            "type": "AwsEc2Instance",
            "tags": {"env": "prod"},
            "partition": "aws",
            "groups": ["compute"],
            "failed_findings_count": 1,
            "inserted_at": "2026-06-01T00:00:00.000000Z",
            "updated_at": "2026-08-13T06:06:00.000000Z",
        },
        "relationships": {
            "provider": {"data": {"type": "providers", "id": PROVIDER_AWS_ID}},
        },
    },
    {
        # A Kubernetes resource. Its provider type is not `aws`, so the AWS
        # correlation matcher must stay null and no REPRESENTS edge may be built.
        "type": "resources",
        "id": RESOURCE_K8S_POD_ID,
        "attributes": {
            "uid": RESOURCE_K8S_POD_UID,
            "name": "synthetic-api-7f9c",
            # Prowler reports the Kubernetes namespace in the region field.
            "region": "default",
            "service": "core",
            "type": "Pod",
            "tags": {},
            "partition": None,
            "groups": ["cluster"],
            "failed_findings_count": 0,
            "inserted_at": "2026-06-02T00:00:00.000000Z",
            "updated_at": "2026-08-12T06:06:00.000000Z",
        },
        "relationships": {
            "provider": {
                "data": {"type": "providers", "id": PROVIDER_KUBERNETES_ID},
            },
        },
    },
    {
        "type": "resources",
        "id": RESOURCE_IAM_USER_ID,
        "attributes": {
            "uid": RESOURCE_IAM_USER_UID,
            "name": "synthetic-user",
            "region": "us-east-1",
            "service": "iam",
            "type": "AwsIamUser",
            "tags": {},
            "partition": "aws",
            "groups": [],
            "failed_findings_count": 1,
            "inserted_at": "2026-06-01T00:00:00.000000Z",
            "updated_at": "2026-08-13T06:06:00.000000Z",
        },
        "relationships": {
            "provider": {"data": {"type": "providers", "id": PROVIDER_AWS_ID}},
        },
    },
]


FINDINGS: list[dict[str, Any]] = [
    {
        # This finding names two resources, which exercises the one-to-many
        # AFFECTS edge.
        "type": "findings",
        "id": FINDING_BUCKET_PUBLIC_ID,
        "attributes": {
            "uid": FINDING_BUCKET_PUBLIC_UID,
            "delta": "new",
            "status": "FAIL",
            "status_extended": (
                "S3 Bucket synthetic-prowler-bucket has public access enabled."
            ),
            "severity": "critical",
            "check_id": "s3_bucket_public_access",
            "categories": ["internet-exposed", "internet-exposed"],
            "resource_groups": "storage",
            "muted": False,
            "muted_reason": None,
            "triage_status": "open",
            "first_seen_at": "2026-07-01T06:00:00.000000Z",
            "inserted_at": "2026-08-13T06:06:00.000000Z",
            "updated_at": "2026-08-13T06:06:00.000000Z",
            "check_metadata": {
                "checktitle": "Ensure S3 buckets are not publicly accessible",
                "description": (
                    "Check whether an S3 bucket grants access to everyone."
                ),
                "servicename": "s3",
                "resourcetype": "AwsS3Bucket",
                "risk": "Public buckets expose their objects to the internet.",
                "categories": ["internet-exposed"],
                "relatedto": [],
                "checkaliases": ["s3_bucket_public"],
                "compliance": {
                    "CIS-2.0": ["2.1.5"],
                    "SOC2": ["CC6.1"],
                },
                "remediation": {
                    "code": {
                        "cli": (
                            "aws s3api put-public-access-block --bucket "
                            "synthetic-prowler-bucket --public-access-block-"
                            "configuration BlockPublicAcls=true"
                        ),
                        "terraform": (
                            'resource "aws_s3_bucket_public_access_block" "x" {}'
                        ),
                        "nativeiac": None,
                        "other": None,
                    },
                    "recommendation": {
                        "text": "Block all public access on the bucket.",
                        "url": "https://docs.prowler.example/checks/s3-public",
                    },
                },
            },
        },
        "relationships": {
            "scan": {"data": {"type": "scans", "id": SCAN_AWS_ID}},
            "resources": {
                "data": [
                    {"type": "resources", "id": RESOURCE_BUCKET_ID},
                    {"type": "resources", "id": RESOURCE_INSTANCE_ID},
                ],
            },
        },
    },
    {
        "type": "findings",
        "id": FINDING_BUCKET_ENCRYPTED_ID,
        "attributes": {
            "uid": FINDING_BUCKET_ENCRYPTED_UID,
            "delta": None,
            "status": "PASS",
            "status_extended": (
                "S3 Bucket synthetic-prowler-bucket has default encryption."
            ),
            "severity": "informational",
            "check_id": "s3_bucket_default_encryption",
            "categories": [],
            "resource_groups": "storage",
            "muted": True,
            "muted_reason": "Accepted by the storage team.",
            "triage_status": "risk_accepted",
            "first_seen_at": "2026-07-01T06:00:00.000000Z",
            "inserted_at": "2026-08-13T06:06:00.000000Z",
            "updated_at": "2026-08-13T06:06:00.000000Z",
            "check_metadata": {
                "checktitle": "Ensure S3 buckets have default encryption enabled",
                "description": (
                    "Check whether an S3 bucket has server-side encryption on."
                ),
                "servicename": "s3",
                "resourcetype": "AwsS3Bucket",
                "risk": "Unencrypted objects are readable if the media leaks.",
                "categories": ["encryption"],
                "relatedto": [],
                "checkaliases": [],
                "compliance": {"CIS-2.0": ["2.1.1"]},
                "remediation": {
                    "code": {
                        "cli": None,
                        "terraform": None,
                        "nativeiac": None,
                        "other": None,
                    },
                    "recommendation": {
                        "text": "Enable default encryption on the bucket.",
                        "url": "https://docs.prowler.example/checks/s3-encryption",
                    },
                },
            },
        },
        "relationships": {
            "scan": {"data": {"type": "scans", "id": SCAN_AWS_ID}},
            "resources": {
                "data": [{"type": "resources", "id": RESOURCE_BUCKET_ID}],
            },
        },
    },
    {
        "type": "findings",
        "id": FINDING_IAM_USER_ID,
        "attributes": {
            "uid": FINDING_IAM_USER_UID,
            "delta": "changed",
            "status": "FAIL",
            "status_extended": "IAM user synthetic-user does not have MFA enabled.",
            "severity": "medium",
            "check_id": "iam_user_mfa_enabled",
            "categories": ["identity"],
            "resource_groups": "identity",
            "muted": False,
            "muted_reason": None,
            "triage_status": "resolved",
            "first_seen_at": "2026-07-02T06:00:00.000000Z",
            "inserted_at": "2026-08-13T06:06:00.000000Z",
            "updated_at": "2026-08-13T06:06:00.000000Z",
            "check_metadata": {
                "checktitle": "Ensure IAM users have MFA enabled",
                "description": "Check whether an IAM user has an MFA device.",
                "servicename": "iam",
                "resourcetype": "AwsIamUser",
                "risk": "A password-only user is one credential leak from misuse.",
                "categories": ["identity"],
                "relatedto": [CVE_ID],
                "checkaliases": [],
                "compliance": {"CIS-2.0": ["1.10"], "ISO27001-2022": ["A.5.17"]},
                "remediation": {
                    "code": {
                        "cli": "aws iam enable-mfa-device --user-name synthetic-user",
                        "terraform": None,
                        "nativeiac": None,
                        "other": None,
                    },
                    "recommendation": {
                        "text": "Enroll the user in an MFA device.",
                        "url": "https://docs.prowler.example/checks/iam-mfa",
                    },
                },
            },
        },
        "relationships": {
            "scan": {"data": {"type": "scans", "id": SCAN_AWS_ID}},
            "resources": {
                "data": [{"type": "resources", "id": RESOURCE_IAM_USER_ID}],
            },
        },
    },
]


# Compliance overviews are fetched one provider at a time, because the objects
# carry no relationship back to the provider they describe. The GitHub provider
# reports none, which exercises a provider with an empty compliance collection.
COMPLIANCE_OVERVIEWS_BY_PROVIDER: dict[str, list[dict[str, Any]]] = {
    PROVIDER_AWS_ID: [
        {
            "type": "compliance-overviews",
            "id": COMPLIANCE_AWS_CIS_OBJECT_ID,
            "attributes": {
                "id": COMPLIANCE_AWS_CIS_ID,
                "framework": "CIS",
                "version": "2.0",
                "requirements_passed": 42,
                "requirements_failed": 7,
                "requirements_manual": 3,
                "total_requirements": 52,
            },
        },
        {
            # Prowler ships the SOC 2 framework without a version, so the
            # attribute is present but empty. It must normalize to null.
            "type": "compliance-overviews",
            "id": COMPLIANCE_AWS_SOC2_OBJECT_ID,
            "attributes": {
                "id": COMPLIANCE_AWS_SOC2_ID,
                "framework": "SOC2",
                "version": "",
                "requirements_passed": 25,
                "requirements_failed": 12,
                "requirements_manual": 5,
                "total_requirements": 42,
            },
        },
    ],
    PROVIDER_KUBERNETES_ID: [
        {
            "type": "compliance-overviews",
            "id": COMPLIANCE_K8S_CIS_OBJECT_ID,
            "attributes": {
                "id": COMPLIANCE_K8S_CIS_ID,
                "framework": "CIS",
                "version": "1.10",
                "requirements_passed": 18,
                "requirements_failed": 4,
                "requirements_manual": 6,
                "total_requirements": 28,
            },
        },
    ],
    PROVIDER_GITHUB_ID: [],
}
