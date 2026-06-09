import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.port_forward import UnifiPortForwardSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi port forwards from the controller.

    :param controller: Controller instance
    :return: List of port forward data
    """
    logger.debug("Fetching UniFi port forwards")
    await controller.port_forwarding.update()

    # Convert aiounifi PortForward objects to dictionaries
    port_forwards = []
    for pf in controller.port_forwarding.values():
        port_forwards.append(
            {
                "id": pf.id,
                "name": pf.name,
                "enabled": pf.enabled,
                "destination_port": pf.destination_port,
                "forward_port": pf.forward_port,
                "forward_ip": pf.forward_ip,
                "protocol": pf.protocol,
                "interface": pf.port_forward_interface,
                "source": pf.source,
            }
        )
    logger.debug("Fetched %d UniFi port forwards", len(port_forwards))
    return port_forwards


@timeit
def load_port_forwards(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi port forwards into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of port forward data
    :param site_id: Site ID for the port forwards
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi port forwards to the graph.", len(data))
    load(
        neo4j_session,
        UnifiPortForwardSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi port forwards from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi port forward cleanup job")
    GraphJob.from_node_schema(UnifiPortForwardSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi port forwards.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    port_forwards = await get(controller)
    load_port_forwards(
        neo4j_session, port_forwards, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
