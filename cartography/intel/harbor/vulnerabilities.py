import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.harbor.util import encode_repository_name
from cartography.intel.harbor.util import get_json
from cartography.intel.harbor.util import pick_report
from cartography.intel.harbor.util import VULNERABILITY_REPORT_MIME_PREFIX
from cartography.intel.trivy.util import canonical_cve_id
from cartography.models.harbor.vulnerability import HarborVulnerabilitySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    instance_id: str,
    images: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync the vulnerabilities Harbor's scanner found in each scanned image.

    Only images whose last scan completed are fetched. Manifest lists are skipped:
    Harbor aggregates the findings of their children, which are reported on their own.
    """
    findings: list[dict[str, Any]] = []
    for image in images:
        if image["type"] != "image" or image["scan_status"] != "Success":
            continue
        logger.debug("Fetching Harbor vulnerabilities for image %s", image["id"])
        report = get(session, base_url, image)
        findings.extend(transform(report, image))
    load_vulnerabilities(neo4j_session, findings, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    session: requests.Session, base_url: str, image: dict[str, Any]
) -> dict[str, Any]:
    path = (
        f"/projects/{image['project_name']}/repositories/"
        f"{encode_repository_name(image['repository_path'])}/artifacts/"
        f"{image['digest']}/additions/vulnerabilities"
    )
    return get_json(session, base_url, path)


def transform(report: dict[str, Any], image: dict[str, Any]) -> list[dict[str, Any]]:
    body = pick_report(report, VULNERABILITY_REPORT_MIME_PREFIX)
    if body is None:
        return []
    findings: dict[str, dict[str, Any]] = {}
    for item in body.get("vulnerabilities") or []:
        vulnerability_id = item["id"]
        cve_id = canonical_cve_id(vulnerability_id)
        finding_id = (
            f"{image['id']}|{vulnerability_id}|{item['package']}|{item['version']}"
        )
        cvss = item.get("preferred_cvss") or {}
        findings[finding_id] = {
            "id": finding_id,
            "vulnerability_id": vulnerability_id,
            "cve_id": cve_id,
            "has_cve": "true" if cve_id else "false",
            "package": item["package"],
            "installed_version": item["version"],
            "fix_version": item.get("fix_version") or None,
            "severity": (item.get("severity") or "Unknown").upper(),
            "status": item.get("status") or None,
            "description": item.get("description"),
            "links": item.get("links") or [],
            "cwe_ids": item.get("cwe_ids") or [],
            "cvss_v3_score": cvss.get("score_v3"),
            "cvss_v3_vector": cvss.get("vector_v3") or None,
            "cvss_v2_score": cvss.get("score_v2"),
            "cvss_v2_vector": cvss.get("vector_v2") or None,
            "image_id": image["id"],
            "image_digest": image["digest"],
            # Matches HarborPackage ids, so the finding links to the SBOM package.
            "package_node_id": f"{image['id']}|{item['package']}|{item['version']}",
        }
    return list(findings.values())


def load_vulnerabilities(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    instance_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HarborVulnerabilitySchema(),
        data,
        lastupdated=update_tag,
        INSTANCE_ID=instance_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(HarborVulnerabilitySchema(), common_job_parameters).run(
        neo4j_session
    )
