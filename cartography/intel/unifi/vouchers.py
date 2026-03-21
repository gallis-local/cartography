import logging
from typing import Any

import neo4j
from aiounifi.controller import Controller

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.voucher import UnifiVoucherSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get(controller: Controller) -> list[dict[str, Any]]:
    """
    Retrieve UniFi vouchers from the controller.

    :param controller: Controller instance
    :return: List of voucher data
    """
    logger.debug("Fetching UniFi vouchers")
    await controller.vouchers.update()
    # controller.vouchers is already scoped to the configured site via
    # /api/s/{site}/stat/voucher — no need to filter by site_id here.
    vouchers = []
    for voucher in controller.vouchers.values():
        vouchers.append(
            {
                "id": voucher.id,
                "code": voucher.code,
                "note": voucher.raw.get("note"),
                "quota": voucher.raw.get("quota"),
                "duration": voucher.raw.get("duration"),
                "qos_overwrite": voucher.raw.get("qos_overwrite", False),
                "qos_usage_quota": voucher.raw.get("qos_usage_quota"),
                "qos_rate_max_up": voucher.raw.get("qos_rate_max_up"),
                "qos_rate_max_down": voucher.raw.get("qos_rate_max_down"),
                "used": voucher.raw.get("used", 0),
                "create_time": voucher.raw.get("create_time"),
                "start_time": voucher.raw.get("start_time"),
                "end_time": voucher.raw.get("end_time"),
                "for_hotspot": voucher.raw.get("for_hotspot", False),
                "admin_name": voucher.raw.get("admin_name"),
                "status": voucher.raw.get("status"),
                "status_expires": voucher.raw.get("status_expires"),
            }
        )
    logger.debug("Fetched %d UniFi vouchers", len(vouchers))
    return vouchers


@timeit
def load_vouchers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load UniFi vouchers into Neo4j.

    :param neo4j_session: Neo4j session
    :param data: List of voucher data
    :param site_id: Site ID for the vouchers
    :param update_tag: Update tag for the sync
    """
    logger.debug("Loading %d UniFi vouchers to the graph.", len(data))
    load(
        neo4j_session,
        UnifiVoucherSchema(),
        data,
        lastupdated=update_tag,
        site_id=site_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale UniFi vouchers from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    """
    logger.debug("Running UniFi voucher cleanup job")
    GraphJob.from_node_schema(UnifiVoucherSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Controller,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync UniFi vouchers.

    :param neo4j_session: Neo4j session
    :param controller: Controller instance
    :param common_job_parameters: Common job parameters
    """
    site_id = common_job_parameters["site_id"]
    vouchers = await get(controller)
    load_vouchers(neo4j_session, vouchers, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
