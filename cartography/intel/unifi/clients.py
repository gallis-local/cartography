import logging
from typing import Any

import neo4j
from unificontrol import UnifiClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.client import UnifiClientSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: UnifiClient) -> list[dict[str, Any]]:
    """
    Retrieve UniFi clients from the controller.

    :param client: UnifiClient instance
    :return: List of client data
    """
    logger.info("Fetching UniFi clients")
    return client.list_clients()


@timeit
def load_clients(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load UniFi clients into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of client data
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi clients into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiClientSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi clients from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiClientSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: UnifiClient,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi clients.

    :param neo4j_session: Neo4j session
    :param client: UnifiClient instance
    :param common_job_parameters: Common job parameters
    :return: List of client data
    """
    clients = get(client)
    load_clients(neo4j_session, clients, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return clients
