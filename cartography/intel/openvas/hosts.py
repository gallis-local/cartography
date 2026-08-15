"""
OpenVAS host ingestion.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.openvas.hosts import OpenVASHostSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _transform_host(host: Any) -> dict:
    latest_scan = host.find("latest_scan")
    task_id = None
    task_name = None
    latest_scan_date = None
    if latest_scan is not None:
        latest_scan_date = latest_scan.findtext("date")
        task = latest_scan.find("task")
        if task is not None:
            task_id = task.get("id")
            task_name = task.findtext("name")

    asset = host.find("asset")
    asset_id = asset.get("id") if asset is not None else None

    severity = host.findtext("severity")
    try:
        severity = float(severity) if severity else None
    except ValueError:
        severity = None

    return {
        "id": host.get("id"),
        "name": host.findtext("name"),
        "ip": host.findtext("ip"),
        "hostname": host.findtext("hostname"),
        "os": host.findtext("os"),
        "comment": host.findtext("comment"),
        "creation_time": host.findtext("creation_time"),
        "modification_time": host.findtext("modification_time"),
        "severity": severity,
        "asset_id": asset_id,
        "latest_scan_date": latest_scan_date,
        "latest_scan_task_id": task_id,
        "latest_scan_task_name": task_name,
        "source_type": host.findtext("source_type"),
        "identifiers": host.findtext("identifiers"),
    }


def transform_hosts(hosts: list) -> list:
    return [_transform_host(host) for host in hosts]


@timeit
def load_hosts(
    neo4j_session: neo4j.Session,
    hosts: list,
    instance_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OpenVASHostSchema(),
        hosts,
        lastupdated=update_tag,
        OPENVAS_INSTANCE_ID=instance_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running OpenVAS host cleanup job")
    GraphJob.from_node_schema(
        OpenVASHostSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    gmp: Any,
    instance_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync OpenVAS hosts into the graph.
    """
    logger.info("Syncing OpenVAS hosts")
    raw_hosts = _get_hosts(gmp)
    hosts = transform_hosts(raw_hosts)
    load_hosts(neo4j_session, hosts, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


def _get_hosts(gmp: Any) -> list:
    from cartography.intel.openvas import api

    return api.get_hosts(gmp)
