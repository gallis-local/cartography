import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
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
    logger.debug("Fetching UniFi sites")
    await controller.sites.update()

    # Convert aiounifi Site objects to dictionaries
    sites = []
    for site in controller.sites.values():
        sites.append(
            {
                "id": site.site_id,
                "name": site.name,
                "desc": site.description,
                "role": getattr(site, "role", "admin"),
            }
        )
    logger.debug("Fetched %d UniFi sites", len(sites))
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
    logger.debug("Loading %d UniFi sites to the graph.", len(data))
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

    UnifiSite is a root tenant node with no sub_resource_relationship and no
    other_relationships, so GraphJob.from_node_schema generates an empty job.
    We use a direct Cypher query instead so that sites removed from the
    controller are properly cleaned up.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi site cleanup job")
    run_write_query(
        neo4j_session,
        "MATCH (s:UnifiSite) WHERE s.lastupdated <> $UPDATE_TAG DETACH DELETE s",
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi sites.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    sites = await get(controller)
    load_sites(neo4j_session, sites, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
