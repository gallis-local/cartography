import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.dpi_app import UnifiDPIAppSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller, site_id: str) -> list[dict[str, Any]]:
    """
    Retrieve UniFi DPI apps from the controller.

    :param controller: Controller instance
    :param site_id: Site ID for the DPI apps
    :return: List of DPI app data
    """
    logger.info("Fetching UniFi DPI apps")
    await controller.dpi_apps.update()

    # Convert aiounifi DPIRestrictionApp objects to dictionaries
    dpi_apps = []
    for app in controller.dpi_apps.values():
        dpi_apps.append(
            {
                "id": app.id,
                "blocked": app.blocked,
                "enabled": app.enabled,
                "log": app.log,
                "site_id": site_id,
            }
        )
    return dpi_apps


@timeit
def load_dpi_apps(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi DPI apps into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of DPI app data
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi DPI apps into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiDPIAppSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi DPI apps from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiDPIAppSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    site_id: str,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi DPI apps.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param site_id: Site ID for the DPI apps
    :param common_job_parameters: Common job parameters
    :return: List of DPI app data
    """
    dpi_apps = await get(controller, site_id)
    load_dpi_apps(neo4j_session, dpi_apps, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup_params = {**common_job_parameters, "site_id": site_id}
    cleanup(neo4j_session, cleanup_params)
    return dpi_apps
