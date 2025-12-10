import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.unifi.voucher import UnifiVoucherSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
async def get(controller: Any, site_id: str) -> list[dict[str, Any]]:
    """
    Get vouchers from UniFi controller
    """
    await controller.vouchers.update()
    vouchers = []
    for voucher in controller.vouchers.values():
        if voucher.site_id == site_id:
            vouchers.append(voucher.raw)
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
        SITE_ID=site_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    """
    Remove vouchers that were not updated in this run
    """
    logger.debug("Running UniFi voucher cleanup job")
    GraphJob.from_node_schema(UnifiVoucherSchema(), common_job_parameters).run(neo4j_session)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    controller: Any,
    site_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync vouchers from UniFi controller to Neo4j
    """
    vouchers = await get(controller, site_id)
    load_vouchers(neo4j_session, vouchers, site_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
