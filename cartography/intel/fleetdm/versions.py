import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fleetdm.utils import paginated_get
from cartography.models.fleetdm.software_version import FleetDMSoftwareVersionSchema
from cartography.models.fleetdm.vulnerability import FleetDMVulnerabilitySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_VERSIONS_URL = "/api/v1/fleet/software/versions"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting FleetDM software versions sync")
    raw_versions = get(api_session, base_url)
    versions_data, vulnerability_data = transform(raw_versions, update_tag)
    load_versions(neo4j_session, versions_data, tenant_id, update_tag)
    if vulnerability_data:
        load_vulnerabilities(
            neo4j_session,
            vulnerability_data,
            tenant_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed FleetDM software versions sync")


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}{_VERSIONS_URL}"
    params = {"vulnerable": "true"}
    return list(paginated_get(api_session, url, params=params))


def transform(
    api_result: list[dict[str, Any]],
    update_tag: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    versions: list[dict[str, Any]] = []
    vulnerabilities: list[dict[str, Any]] = []

    for version in api_result:
        vuln_list = version.get("vulnerabilities") or []
        versions.append(
            {
                "id": str(version.get("id")),
                "name": version.get("name"),
                "version": version.get("version"),
                "source": version.get("source"),
                "release": version.get("release"),
                "platform": version.get("platform"),
                "vendor": version.get("vendor"),
                "arch": version.get("arch"),
                "generated_cpe": version.get("generated_cpe"),
                "hosts_count": version.get("hosts_count"),
                "browser": version.get("browser"),
                "extension_id": version.get("extension_id"),
                "vulnerabilities_count": len(vuln_list),
            }
        )

        version_id = str(version.get("id"))
        for vuln in vuln_list:
            cve = vuln.get("cve", "")
            vulnerabilities.append(
                {
                    "id": f"{version_id}-{cve}",
                    "cve_id": cve,
                    "details_link": vuln.get("details_link"),
                    "cvss_score": vuln.get("cvss_score"),
                    "epss_probability": vuln.get("epss_probability"),
                    "cisa_known_exploit": vuln.get("cisa_known_exploit", False),
                    "cve_published": vuln.get("cve_published"),
                    "cve_description": vuln.get("cve_description"),
                    "resolved_in_version": vuln.get("resolved_in_version"),
                    "software_version_id": version_id,
                }
            )

    return versions, vulnerabilities


@timeit
def load_versions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMSoftwareVersionSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def load_vulnerabilities(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMVulnerabilitySchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        FleetDMSoftwareVersionSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        FleetDMVulnerabilitySchema(),
        common_job_parameters,
    ).run(neo4j_session)
