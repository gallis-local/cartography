import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.site import UnifiSiteSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi sites from the controller.

    :param controller: Controller instance
    :return: List of site data
    """
    logger.info("Fetching UniFi sites")
    await controller.sites.update()

    # Convert aiounifi Site objects to dictionaries
    sites = []
    for site in controller.sites.values():
        sites.append(
            {
                "_id": site.id,
                "name": site.name,
                "desc": getattr(site, "desc", site.name),
                "role": getattr(site, "role", "admin"),
            }
        )
    return sites


@timeit
def load_sites(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load UniFi sites into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of site data
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi sites into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiSiteSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi sites from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiSiteSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi sites.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    :return: List of site data
    """
    sites = await get(controller)
    load_sites(neo4j_session, sites, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return sites
