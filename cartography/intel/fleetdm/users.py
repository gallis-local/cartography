import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fleetdm.utils import paginated_get
from cartography.models.fleetdm.user import FleetDMUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_USERS_URL = "/api/v1/fleet/users"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting FleetDM users sync")
    users = get(api_session, base_url)
    transformed = transform(users)
    load_users(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed FleetDM users sync")


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}{_USERS_URL}"
    return list(paginated_get(api_session, url))


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for user in api_result:
        result.append(
            {
                "id": str(user.get("id")),
                "name": user.get("name"),
                "email": user.get("email"),
                "global_role": user.get("global_role"),
                "sso_enabled": user.get("sso_enabled"),
                "mfa_enabled": user.get("mfa_enabled"),
                "api_only": user.get("api_only"),
                "force_password_reset": user.get("force_password_reset"),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at"),
            }
        )
    return result


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMUserSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FleetDMUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
