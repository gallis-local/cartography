import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fleetdm.utils import paginated_get
from cartography.models.fleetdm.software import FleetDMSoftwareSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_SOFTWARE_URL = "/api/v1/fleet/software/titles"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting FleetDM software sync")
    software_titles = get(api_session, base_url)
    transformed = transform(software_titles)
    load_software(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed FleetDM software sync")


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}{_SOFTWARE_URL}"
    return list(paginated_get(api_session, url))


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for title in api_result:
        result.append(
            {
                "id": str(title.get("id")),
                "name": title.get("name"),
                "source": title.get("source"),
                "browser": title.get("browser"),
                "hosts_count": title.get("hosts_count"),
                "versions_count": title.get("versions_count"),
                "bundle_identifier": title.get("bundle_identifier"),
                "display_name": title.get("display_name"),
            }
        )
    return result


@timeit
def load_software(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMSoftwareSchema(),
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
        FleetDMSoftwareSchema(),
        common_job_parameters,
    ).run(neo4j_session)
