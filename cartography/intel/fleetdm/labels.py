import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fleetdm.utils import paginated_get
from cartography.models.fleetdm.label import FleetDMLabelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_LABELS_URL = "/api/v1/fleet/labels"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting FleetDM labels sync")
    labels = get(api_session, base_url)
    transformed = transform(labels)
    load_labels(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed FleetDM labels sync")


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}{_LABELS_URL}"
    return list(paginated_get(api_session, url))


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for label in api_result:
        result.append(
            {
                "id": str(label.get("id")),
                "name": label.get("name"),
                "description": label.get("description"),
                "query": label.get("query"),
                "platform": label.get("platform"),
                "label_type": label.get("label_type"),
                "label_membership_type": label.get("label_membership_type"),
                "host_count": label.get("host_count"),
                "created_at": label.get("created_at"),
                "updated_at": label.get("updated_at"),
            }
        )
    return result


@timeit
def load_labels(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMLabelSchema(),
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
        FleetDMLabelSchema(),
        common_job_parameters,
    ).run(neo4j_session)
