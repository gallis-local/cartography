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


def _transform_host(asset: Any) -> dict:
    """
    Transform a <get_assets type="host"> response element.

    GMP's get_hosts is a thin wrapper around get_assets(type="host"): each
    item is an <asset> element (identified by asset id, not a separate host
    id) with a nested <host> element carrying severity/detail, and an
    <identifiers> list of <identifier><name>ip|hostname|OS</name><value>
    entries scraped from scan reports. There is no latest_scan/task
    reference in this API version, so LAST_SCANNED_BY stays unset.
    """
    identifiers = asset.find("identifiers")
    ip = None
    hostname = None
    identifier_names: list[str] = []
    if identifiers is not None:
        for identifier in identifiers.findall("identifier"):
            id_name = identifier.findtext("name")
            id_value = identifier.findtext("value")
            if id_name and id_name not in identifier_names:
                identifier_names.append(id_name)
            if id_name == "ip" and ip is None:
                ip = id_value
            elif id_name == "hostname" and hostname is None:
                hostname = id_value

    host = asset.find("host")
    severity = None
    os_name = None
    if host is not None:
        severity_elem = host.find("severity")
        severity_text = (
            severity_elem.findtext("value") if severity_elem is not None else None
        )
        try:
            severity = float(severity_text) if severity_text else None
        except ValueError:
            severity = None
        for detail in host.findall("detail"):
            if detail.findtext("name") == "best_os_txt":
                os_name = detail.findtext("value")
                break

    asset_id = asset.get("id")
    resolved_ip = ip or asset.findtext("name")

    return {
        # Keyed by IP, not GMP's asset id: GVM issues a fresh asset id per
        # host (re)discovery, so keying on asset_id creates a new duplicate
        # OpenVASHost node -- sometimes several per sync -- for the same IP
        # instead of updating one. IP is what every relationship (AFFECTS,
        # dashboards) already joins hosts on, so it's the real identity here.
        "id": resolved_ip,
        "name": asset.findtext("name"),
        "ip": resolved_ip,
        "hostname": hostname,
        "os": os_name,
        "comment": asset.findtext("comment"),
        "creation_time": asset.findtext("creation_time"),
        "modification_time": asset.findtext("modification_time"),
        "severity": severity,
        "asset_id": asset_id,
        "latest_scan_date": None,
        "latest_scan_task_id": None,
        "latest_scan_task_name": None,
        "source_type": asset.findtext("type"),
        "identifiers": ",".join(identifier_names) or None,
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
