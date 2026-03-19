import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.admin import UnifiAdminSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi admins from the controller.

    :param controller: Controller instance
    :return: List of admin data
    """
    logger.debug("Fetching UniFi admins")
    await controller.admins.update()

    admins = []
    for admin in controller.admins.values():
        admins.append(
            {
                "id": admin.raw["_id"],
                "name": admin.raw.get("name"),
                "email": admin.raw.get("email") or None,
                "role": admin.raw.get("role"),
                "is_super_admin": admin.raw.get("is_super_admin", False),
                "last_site_name": admin.raw.get("last_site_name"),
            }
        )
    return admins


@timeit
def load_admins(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi admins into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of admin data
    :param site_id: Site ID for the admins
    :param update_tag: Update tag for the sync
    """
    load(
        neo4j_session,
        UnifiAdminSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi admins from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi admin cleanup job")
    GraphJob.from_node_schema(UnifiAdminSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi admins.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    admins = await get(controller)
    load_admins(neo4j_session, admins, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
