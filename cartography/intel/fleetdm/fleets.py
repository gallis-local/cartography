import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fleetdm.utils import paginated_get
from cartography.models.fleetdm.fleet import FleetDMFleetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_FLEETS_URL = "/api/v1/fleet/fleets"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting FleetDM fleets sync")

    try:
        fleets = get(api_session, base_url)
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        logger.warning(
            "FleetDM fleets endpoint returned HTTP %s "
            "(this is expected on Fleet CE without Premium license). "
            "Skipping fleets sync.",
            status,
        )
        return

    transformed = transform(fleets)
    load_fleets(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed FleetDM fleets sync")


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}{_FLEETS_URL}"
    return list(paginated_get(api_session, url))


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for fleet in api_result:
        result.append(
            {
                "id": str(fleet.get("id")),
                "name": fleet.get("name"),
                "description": fleet.get("description"),
                "host_count": fleet.get("host_count"),
                "user_count": fleet.get("user_count"),
                "created_at": fleet.get("created_at"),
                "updated_at": fleet.get("updated_at"),
            }
        )
    return result


@timeit
def load_fleets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMFleetSchema(),
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
        FleetDMFleetSchema(),
        common_job_parameters,
    ).run(neo4j_session)
