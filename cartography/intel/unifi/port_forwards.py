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
    :param update_tag: Update tag for the sync
    """
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
    GraphJob.from_node_schema(UnifiPortForwardSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi port forwards.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    :return: List of port forward data
    """
    site_id = common_job_parameters["site_id"]
    port_forwards = await get(controller)
    load_port_forwards(
        neo4j_session, port_forwards, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
    return port_forwards
