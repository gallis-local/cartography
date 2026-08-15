"""
OpenVAS result (finding) and NVT ingestion.

NVTs are only ingested for the NVTs that were actually detected in results —
never the full NVT feed, which would pull tens of thousands of unused nodes.
"""

import logging
from datetime import UTC
from datetime import datetime
from typing import Any
from typing import Optional

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.openvas.results import OpenVASNVTSchema
from cartography.models.openvas.results import OpenVASResultSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _parse_tags(tags: Optional[str]) -> dict:
    """
    Parse a GVM tags string ("key1=value1;key2=value2") into a dict.
    """
    result: dict[str, str] = {}
    if not tags:
        return result
    for part in tags.split(";"):
        if "=" in part:
            key, _, value = part.partition("=")
            result[key.strip()] = value.strip()
    return result


def _extract_cves(nvt: Any) -> list:
    """
    Collect CVE ids from the nvt element: the <cve> element, refs of type cve,
    and the cve_id tag.
    """
    cves: list[str] = []
    cve_elem = nvt.findtext("cve")
    if cve_elem:
        cves.extend(cve.strip() for cve in cve_elem.split(",") if cve.strip())
    for ref in nvt.findall("refs/ref"):
        if ref.get("type") == "cve" and ref.get("id"):
            cves.append(ref.get("id"))
    tags = _parse_tags(nvt.findtext("tags"))
    if tags.get("cve_id"):
        cves.extend(cve.strip() for cve in tags["cve_id"].split(",") if cve.strip())
    # Dedupe while preserving order.
    return list(dict.fromkeys(cves))


def _transform_nvt(nvt: Any) -> dict:
    oid = nvt.get("id") or nvt.get("oid")
    qod = nvt.find("qod")
    tags = _parse_tags(nvt.findtext("tags"))
    cves = _extract_cves(nvt)

    return {
        "id": oid,
        "name": nvt.findtext("name"),
        "oid": oid,
        "family": nvt.findtext("family"),
        "severity": nvt.findtext("severity"),
        "cvss_base": nvt.findtext("cvss_base"),
        "cvss_base_vector": tags.get("cvss_base_vector"),
        "solution": nvt.findtext("solution"),
        "qod": qod.get("value") if qod is not None else None,
        "qod_type": qod.get("type") if qod is not None else None,
        "description": nvt.findtext("description"),
        "cve_list": cves if cves else None,
        "tags": nvt.findtext("tags"),
    }


def _transform_result(result: Any) -> dict:
    nvt = result.find("nvt")
    qod = result.find("qod")
    task = result.find("task")
    tags = _parse_tags(nvt.findtext("tags")) if nvt is not None else {}
    cves = _extract_cves(nvt) if nvt is not None else []

    severity = result.findtext("severity")
    try:
        severity = float(severity) if severity else None
    except ValueError:
        severity = None

    return {
        "id": result.get("id"),
        "name": result.findtext("name"),
        "host": result.findtext("host"),
        "hostname": result.findtext("hostname"),
        "port": result.findtext("port"),
        "nvt_id": nvt.get("id") or nvt.get("oid") if nvt is not None else None,
        "task_id": task.get("id") if task is not None else None,
        "task_name": task.findtext("name") if task is not None else None,
        "severity": severity,
        "threat": result.findtext("threat"),
        "original_threat": result.findtext("original_threat"),
        "qod": qod.get("value") if qod is not None else None,
        "qod_type": qod.get("type") if qod is not None else None,
        "description": result.findtext("description"),
        "summary": tags.get("summary"),
        "detection_result": tags.get("detection_result"),
        "source_ip": result.findtext("source_ip"),
        "created": result.findtext("created"),
        "cve_id": cves[0] if cves else None,
        "cve_list": cves if cves else None,
        "has_cve": "true" if cves else "false",
    }


def transform_results(results: list) -> tuple[list, list]:
    """
    Transform raw result elements into (results, nvts) data lists.

    NVTs are deduped by OID since many results can share the same NVT.
    """
    result_data: list = []
    nvts_by_oid: dict[str, dict] = {}
    for result in results:
        result_data.append(_transform_result(result))
        nvt = result.find("nvt")
        if nvt is not None:
            nvt_data = _transform_nvt(nvt)
            if nvt_data["id"]:
                nvts_by_oid[nvt_data["id"]] = nvt_data
    return result_data, list(nvts_by_oid.values())


@timeit
def load_results_and_nvts(
    neo4j_session: neo4j.Session,
    result_data: list,
    nvt_data: list,
    instance_id: str,
    update_tag: int,
) -> None:
    # NVTs must exist before results so DETECTED_BY edges resolve.
    load(
        neo4j_session,
        OpenVASNVTSchema(),
        nvt_data,
        lastupdated=update_tag,
        OPENVAS_INSTANCE_ID=instance_id,
    )
    load(
        neo4j_session,
        OpenVASResultSchema(),
        result_data,
        lastupdated=update_tag,
        OPENVAS_INSTANCE_ID=instance_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running OpenVAS result cleanup job")
    GraphJob.from_node_schema(
        OpenVASResultSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_results(
    neo4j_session: neo4j.Session,
    gmp: Any,
    instance_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    lookback_days: int = 180,
) -> None:
    """
    Sync OpenVAS results (and their detected NVTs) into the graph.

    Only results created within the lookback window are fetched, matching the
    behavior of the Tenable module.
    """
    logger.info("Syncing OpenVAS results")
    from cartography.intel.openvas import api

    since: Optional[datetime] = None
    if lookback_days:
        since = datetime.fromtimestamp(
            update_tag - lookback_days * 86400,
            tz=UTC,
        )
    raw_results = api.get_results(gmp, since=since)
    result_data, nvt_data = transform_results(raw_results)
    load_results_and_nvts(neo4j_session, result_data, nvt_data, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
