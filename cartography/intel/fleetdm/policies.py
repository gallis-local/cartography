import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fleetdm.utils import paginated_get
from cartography.models.fleetdm.policy import FleetDMPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_POLICIES_URL = "/api/v1/fleet/global/policies"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting FleetDM policies sync")
    policies = get(api_session, base_url)
    transformed = transform(policies)
    load_policies(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed FleetDM policies sync")


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}{_POLICIES_URL}"
    return list(paginated_get(api_session, url))


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for policy in api_result:
        result.append(
            {
                "id": str(policy.get("id")),
                "name": policy.get("name"),
                "query": policy.get("query"),
                "description": policy.get("description"),
                "resolution": policy.get("resolution"),
                "platform": policy.get("platform"),
                "critical": policy.get("critical"),
                "author_id": str(policy["author_id"])
                if policy.get("author_id")
                else None,
                "author_name": policy.get("author_name"),
                "author_email": policy.get("author_email"),
                "team_id": str(policy["team_id"]) if policy.get("team_id") else None,
                "passing_host_count": policy.get("passing_host_count"),
                "failing_host_count": policy.get("failing_host_count"),
                "created_at": policy.get("created_at"),
                "updated_at": policy.get("updated_at"),
            }
        )
    return result


@timeit
def load_policies(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMPolicySchema(),
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
        FleetDMPolicySchema(),
        common_job_parameters,
    ).run(neo4j_session)
