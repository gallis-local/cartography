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
async def get(controller: Controller, site_id: str) -> list[dict[str, Any]]:
    """
    Retrieve UniFi speedtest results from the controller.

    aiounifi has no dedicated speedtest handler/endpoint -- the controller only
    surfaces the most recent speedtest run as a per-device field
    (Device.speedtest_status, sourced from the device's raw "speedtest-status"
    object), typically populated only on gateway devices (UDM/USG/UXG). This
    reads that field off the already-fetched controller.devices collection
    rather than calling a nonexistent controller.speedtest API.

    :param controller: Controller instance
    :param site_id: Site ID the speedtests belong to. Device MACs are unique per
        controller, but folding site_id into the node id keeps identity
        consistent with the rest of this module when multiple sites are synced.
    :return: List of speedtest data
    """
    logger.debug("Fetching UniFi speedtest results")

    speedtests = []
    for device in controller.devices.values():
        speedtest = device.speedtest_status
        if not speedtest:
            continue

        speedtests.append(
            {
                "id": f"{site_id}_{device.mac}",
                "download": speedtest.get("xput_download"),
                "upload": speedtest.get("xput_upload"),
                "ping": speedtest.get("latency"),
                "timestamp": speedtest.get("rundate"),
                "gateway_mac": device.mac,
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
    speedtests = await get(controller, site_id)
    load_speedtests(
        neo4j_session, speedtests, site_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
