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
async def get(controller: Controller, site_id: str) -> list[dict[str, Any]]:
    """
    Get vouchers from UniFi controller
    """
    logger.debug("Fetching UniFi vouchers")
    await controller.vouchers.update()
    vouchers = []
    for voucher in controller.vouchers.values():
        if voucher.site_id == site_id:
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
    return vouchers


@timeit
def load_vouchers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    site_id: str,
    update_tag: int,
) -> None:
    """
    Load vouchers into the graph
    """
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
    Remove vouchers that were not updated in this run
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
    Sync vouchers from UniFi controller to Neo4j
    """
    site_id = common_job_parameters["site_id"]
    vouchers = await get(controller, site_id)
    load_vouchers(neo4j_session, vouchers, site_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
