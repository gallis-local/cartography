import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.speedtest import UnifiSpeedtestSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi speedtest results from the controller.

    :param controller: Controller instance
    :return: List of speedtest data
    """
    logger.debug("Fetching UniFi speedtest results")
    await controller.speedtest.update()

    # Convert aiounifi SpeedtestStatus objects to dictionaries
    # The obj_id_key for speedtest is "interface_name", so the dict keys are interface names
    speedtests = []
    for interface_name, speedtest in controller.speedtest.items():
        # Find the gateway device that ran the speedtest
        # The speedtest is typically run on the gateway (UGW)
        gateway_mac = None
        for device in controller.devices.values():
            if device.type == "ugw" or device.type == "udm":
                gateway_mac = device.mac
                break

        speedtests.append(
            {
                "id": interface_name,
                "interface_name": interface_name,
                "download": speedtest.download,
                "upload": speedtest.upload,
                "ping": speedtest.ping,
                "timestamp": speedtest.timestamp,
                "gateway_mac": gateway_mac,
            }
        )
    logger.debug("Fetched %d UniFi speedtest results", len(speedtests))
    return speedtests


@timeit
def load_speedtests(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi speedtest results into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of speedtest data
    :param site_id: Site ID for the speedtests
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi speedtest results to the graph.", len(data))
    load(
        neo4j_session,
        UnifiSpeedtestSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi speedtest results from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi speedtest cleanup job")
    GraphJob.from_node_schema(UnifiSpeedtestSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi speedtest results.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    speedtests = await get(controller)
    load_speedtests(
        neo4j_session, speedtests, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
