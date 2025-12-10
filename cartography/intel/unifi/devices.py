import logging
from typing import Any

import neo4j
from unificontrol import UnifiClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.device import UnifiDeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: UnifiClient) -> list[dict[str, Any]]:
    """
    Retrieve UniFi devices from the controller.

    :param client: UnifiClient instance
    :return: List of device data
    """
    logger.info("Fetching UniFi devices")
    return client.list_devices_basic()


@timeit
def load_devices(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load UniFi devices into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of device data
    :param update_tag: Update tag for the sync
    """
    logger.info("Loading %d UniFi devices into Neo4j.", len(data))
    load(
        neo4j_session,
        UnifiDeviceSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi devices from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    GraphJob.from_node_schema(UnifiDeviceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: UnifiClient,
    common_job_parameters: dict[str, Any],
) -> list[dict]:
    """
    Sync UniFi devices.

    :param neo4j_session: Neo4j session
    :param client: UnifiClient instance
    :param common_job_parameters: Common job parameters
    :return: List of device data
    """
    devices = get(client)
    load_devices(neo4j_session, devices, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return devices
