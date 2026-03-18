import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.dpi_group import UnifiDPIGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller, site_id: str) -> list[dict[str, Any]]:
    """
    Retrieve UniFi DPI groups from the controller.

    :param controller: Controller instance
    :param site_id: Site ID for the DPI groups
    :return: List of DPI group data
    """
    logger.debug("Fetching UniFi DPI groups")
    await controller.dpi_groups.update()

    # Convert aiounifi DPIRestrictionGroup objects to dictionaries
    dpi_groups = []
    for group in controller.dpi_groups.values():
        dpi_groups.append(
            {
                "id": group.id,
                "name": group.name,
                "attr_no_delete": group.attr_no_delete or False,
                "attr_hidden_id": group.attr_hidden_id or None,
                "dpiapp_ids": group.dpiapp_ids or None,
                "site_id": site_id,
            }
        )
    return dpi_groups


@timeit
def load_dpi_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi DPI groups into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of DPI group data
    :param site_id: Site ID for the DPI groups
    :param update_tag: Update tag for the sync
    """
    load(
        neo4j_session,
        UnifiDPIGroupSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi DPI groups from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiDPIGroupSchema(), common_job_parameters).run(
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
    Sync UniFi DPI groups.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param site_id: Site ID for the DPI groups
    :param common_job_parameters: Common job parameters
    :return: List of DPI group data
    """
    dpi_groups = await get(controller, site_id)
    load_dpi_groups(
        neo4j_session, dpi_groups, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
    return dpi_groups
