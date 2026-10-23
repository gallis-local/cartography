"""Mock Harbor API payloads, keyed by the URL path (after /api/v2.0) they answer."""

from typing import Any

VULN_MIME = "application/vnd.security.vulnerability.report; version=1.1"

NGINX_DIGEST = "sha256:aaaa"
API_AMD64_DIGEST = "sha256:bbbb"
API_ARM64_DIGEST = "sha256:cccc"
API_INDEX_DIGEST = "sha256:dddd"
CHART_DIGEST = "sha256:eeee"

SYSTEM_INFO = {"harbor_version": "v2.11.0"}

PROJECTS = [
    {
        "project_id": 1,
        "name": "library",
        "owner_name": "admin",
        "repo_count": 1,
        "creation_time": "2024-01-01T00:00:00.000Z",
        "update_time": "2024-01-02T00:00:00.000Z",
        "metadata": {"public": "true"},
    },
    {
        "project_id": 2,
        "name": "team",
        "owner_name": "admin",
        "repo_count": 1,
        "creation_time": "2024-02-01T00:00:00.000Z",
        "update_time": "2024-02-02T00:00:00.000Z",
        "metadata": {"public": "false"},
    },
]

REPOSITORIES = {
    "library": [
        {
            "id": 10,
            "name": "library/nginx",
            "project_id": 1,
            "artifact_count": 1,
            "pull_count": 7,
            "creation_time": "2024-01-01T00:00:00.000Z",
            "update_time": "2024-01-02T00:00:00.000Z",
        }
    ],
    "team": [
        {
            "id": 20,
            "name": "team/app/api",
            "project_id": 2,
            "description": "API service",
            "artifact_count": 4,
            "pull_count": 0,
            "creation_time": "2024-02-01T00:00:00.000Z",
            "update_time": "2024-02-02T00:00:00.000Z",
        }
    ],
}


def _scan_overview(status: str, severity: str, total: int, fixable: int) -> dict:
    return {
        VULN_MIME: {
            "report_id": "r1",
            "scan_status": status,
            "severity": severity,
            "end_time": "2024-03-01T00:00:00.000Z",
            "summary": {"total": total, "fixable": fixable},
            "scanner": {"name": "Trivy", "vendor": "Aqua Security", "version": "0.50"},
        }
    }


NGINX_ARTIFACTS = [
    {
        "id": 100,
        "type": "IMAGE",
        "media_type": "application/vnd.docker.container.image.v1+json",
        "manifest_media_type": "application/vnd.docker.distribution.manifest.v2+json",
        "digest": NGINX_DIGEST,
        "size": 1000,
        "push_time": "2024-03-01T00:00:00.000Z",
        "extra_attrs": {"architecture": "amd64", "os": "linux", "author": "nginx"},
        "tags": [
            {"id": 1, "name": "latest", "immutable": False, "signed": True},
            {"id": 2, "name": "1.25", "immutable": True, "signed": False},
        ],
        "scan_overview": _scan_overview("Success", "High", 2, 1),
        "sbom_overview": {
            "scan_status": "Success",
            "sbom_digest": "sha256:sbom1",
            "end_time": "2024-03-01T00:01:00.000Z",
        },
    }
]

TEAM_ARTIFACTS = [
    {
        "id": 200,
        "type": "IMAGE",
        "digest": API_AMD64_DIGEST,
        "size": 500,
        "extra_attrs": {"architecture": "amd64", "os": "linux"},
        "tags": None,
        "scan_overview": _scan_overview("Running", "Unknown", 0, 0),
    },
    {
        "id": 201,
        "type": "IMAGE",
        "digest": API_ARM64_DIGEST,
        "size": 500,
        "extra_attrs": {"architecture": "arm64", "os": "linux", "variant": "v8"},
        "tags": None,
    },
    {
        "id": 202,
        "type": "IMAGE",
        "digest": API_INDEX_DIGEST,
        "size": 1200,
        "references": [
            {"child_digest": API_AMD64_DIGEST, "platform": {"architecture": "amd64"}},
            {"child_digest": API_ARM64_DIGEST, "platform": {"architecture": "arm64"}},
        ],
        "tags": [{"id": 3, "name": "v1", "immutable": False, "signed": False}],
    },
    {"id": 203, "type": "CHART", "digest": CHART_DIGEST, "tags": None},
]

ARTIFACTS = {
    "library/nginx": NGINX_ARTIFACTS,
    "team/app/api": TEAM_ARTIFACTS,
}

NGINX_VULNERABILITIES = {
    VULN_MIME: {
        "generated_at": "2024-03-01T00:00:00.000Z",
        "severity": "High",
        "vulnerabilities": [
            {
                "id": "CVE-2024-0001",
                "package": "openssl",
                "version": "3.0.2",
                "fix_version": "3.0.3",
                "severity": "High",
                "status": "fixed",
                "description": "Buffer overflow in openssl.",
                "links": ["https://avd.aquasec.com/nvd/cve-2024-0001"],
                "cwe_ids": ["CWE-120"],
                "preferred_cvss": {
                    "score_v3": 8.1,
                    "vector_v3": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    "score_v2": None,
                    "vector_v2": "",
                },
            },
            {
                "id": "GHSA-xxxx-yyyy-zzzz",
                "package": "libfoo",
                "version": "1.0",
                "fix_version": "",
                "severity": "Low",
                "description": None,
                "links": None,
                "preferred_cvss": {},
            },
        ],
    }
}

NGINX_SBOM = {
    "spdxVersion": "SPDX-2.3",
    "packages": [
        {
            "name": "library/nginx",
            "SPDXID": "SPDXRef-DocumentRoot-Image",
            "primaryPackagePurpose": "CONTAINER",
        },
        {
            "name": "openssl",
            "versionInfo": "3.0.2",
            "SPDXID": "SPDXRef-Package-openssl",
            "licenseConcluded": "Apache-2.0",
            "supplier": "Organization: Debian",
            "externalRefs": [
                {
                    "referenceType": "purl",
                    "referenceLocator": "pkg:deb/debian/openssl@3.0.2",
                }
            ],
        },
        {
            "name": "libfoo",
            "versionInfo": "1.0",
            "SPDXID": "SPDXRef-Package-libfoo",
            "licenseConcluded": "NOASSERTION",
            "externalRefs": [],
        },
    ],
}

# Path (after /api/v2.0) -> payload. Repository path segments are double-encoded
# exactly the way Harbor expects them.
RESPONSES: dict[str, Any] = {
    "/systeminfo": SYSTEM_INFO,
    "/projects": PROJECTS,
    "/projects/library/repositories": REPOSITORIES["library"],
    "/projects/team/repositories": REPOSITORIES["team"],
    "/projects/library/repositories/nginx/artifacts": NGINX_ARTIFACTS,
    "/projects/team/repositories/app%252Fapi/artifacts": TEAM_ARTIFACTS,
    f"/projects/library/repositories/nginx/artifacts/{NGINX_DIGEST}/additions/vulnerabilities": NGINX_VULNERABILITIES,
    f"/projects/library/repositories/nginx/artifacts/{NGINX_DIGEST}/additions/sbom": NGINX_SBOM,
}
