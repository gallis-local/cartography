"""
OpenVAS result (finding) and NVT ingestion.

NVTs are only ingested for the NVTs that were actually detected in results —
never the full NVT feed, which would pull tens of thousands of unused nodes.
"""

import logging
from datetime import datetime
from datetime import UTC
from typing import Any
from typing import Optional

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.openvas.util import float_or_none
from cartography.models.openvas.results import OpenVASNVTSchema
from cartography.models.openvas.results import OpenVASResultSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _parse_tags(tags: Optional[str]) -> dict:
    """
    Parse a GVM tags string ("key1=value1|key2=value2") into a dict.

    gvmd documents the <tags> element as "pipe-separated syntax" and the values
    themselves routinely contain semicolons and newlines (CVSS vectors, prose
    summaries). Splitting on ";" therefore produced a single bogus entry whose
    value was the whole rest of the string, so every key after the first --
    summary, cve_id, solution_type -- silently went missing.

    :param tags: Raw GVM tags string, or None
    :return: Mapping of tag key to tag value, empty when there are no tags
    """
    result: dict[str, str] = {}
    if not tags:
        return result
    for part in tags.split("|"):
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        # GVM emits every tag key it knows about, most of them empty
        # ("insight=|affected=|impact="). Dropping the empty ones lets
        # tags.get(key) answer None instead of "", so a missing tag is one
        # value graph-wide rather than two.
        if value.strip():
            result[key.strip()] = value.strip()
    return result


def _first_score(*values: Optional[str]) -> Optional[float]:
    """
    Return the first of the given raw score strings that parses to a float.

    A plain `a or b` fallback cannot be used here: a legitimate score of 0.0 is
    falsy, so "no vulnerability" would fall through to the next candidate and
    ultimately read as None.

    :param values: Raw score strings in preference order
    :return: The first parseable score, or None if none parse
    """
    for value in values:
        score = float_or_none(value)
        if score is not None:
            return score
    return None


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
    oid = nvt.get("oid") or nvt.get("id")
    if not oid:
        raise ValueError("OpenVAS NVT element is missing its id/oid attribute")
    tags = _parse_tags(nvt.findtext("tags"))
    cves = _extract_cves(nvt)
    solution = nvt.find("solution")
    # gvmd emits the NVT's numeric score as the `score` attribute of
    # <severities>, never as a <severity> child, so findtext("severity") read
    # null on every NVT. <cvss_base> is the fallback for older gvmd releases.
    severities = nvt.find("severities")

    return {
        "id": oid,
        "name": nvt.findtext("name"),
        "oid": oid,
        "family": nvt.findtext("family"),
        "severity": _first_score(
            severities.get("score") if severities is not None else None,
            nvt.findtext("cvss_base"),
        ),
        "cvss_base": float_or_none(nvt.findtext("cvss_base")),
        "cvss_base_vector": tags.get("cvss_base_vector"),
        # gvmd puts the remediation prose in the solution tag, not in the
        # <solution> element's text, which is empty on every NVT.
        "solution": tags.get("solution") or nvt.findtext("solution") or None,
        # GMP's <solution> element carries the remediation category (e.g.
        # VendorFix, WillNotFix, Mitigation, Workaround, NoneAvailable) and
        # the mechanism to apply it (e.g. DebianAPTUpgrade) as attributes,
        # not text -- see the get_nvts response schema in the GMP protocol
        # docs (https://docs.greenbone.net/API/GMP/gmp-22.5.html#get_nvts).
        # Without these, there was no way to tell "no fix available" apart
        # from "vendor already shipped a fix" without parsing solution prose.
        "solution_type": (solution.get("type") if solution is not None else None)
        or tags.get("solution_type"),
        "solution_method": (solution.get("method") if solution is not None else None)
        or None,
        # gvmd does not emit a <description> child of <nvt>; the human-readable
        # text lives in the summary tag.
        "summary": tags.get("summary"),
        "cve_list": cves if cves else None,
        "tags": nvt.findtext("tags"),
    }


def _transform_result(result: Any) -> dict:
    nvt = result.find("nvt")
    qod = result.find("qod")
    task = result.find("task")
    host = result.find("host")
    tags = _parse_tags(nvt.findtext("tags")) if nvt is not None else {}
    cves = _extract_cves(nvt) if nvt is not None else []

    result_id = result.get("id")
    if not result_id:
        raise ValueError("OpenVAS result element is missing its id attribute")

    return {
        "id": result_id,
        "name": result.findtext("name"),
        # <host> carries the IP as its own text plus <asset> and <hostname>
        # children, so the hostname has to be read one level down; reading it
        # as a direct child of <result> left it null on every finding.
        "host": (host.text or "").strip() or None if host is not None else None,
        "hostname": host.findtext("hostname") if host is not None else None,
        "port": result.findtext("port"),
        "nvt_id": nvt.get("oid") or nvt.get("id") if nvt is not None else None,
        "task_id": task.get("id") if task is not None else None,
        "task_name": task.findtext("name") if task is not None else None,
        "severity": float_or_none(result.findtext("severity")),
        "threat": result.findtext("threat"),
        "original_threat": result.findtext("original_threat"),
        # gvmd emits QoD as <qod><value/><type/></qod>, not as attributes of
        # <qod>. Reading attributes left the Quality of Detection null on every
        # finding, which is the field that separates a confirmed exploit from a
        # banner guess -- the difference between triage and noise.
        "qod": float_or_none(qod.findtext("value")) if qod is not None else None,
        "qod_type": qod.findtext("type") if qod is not None else None,
        "description": result.findtext("description"),
        "summary": tags.get("summary"),
        # GMP results carry their timestamp as <creation_time>, matching
        # every other entity (task/target/config/...) -- not <created>,
        # which is only a get_results *filter* keyword, not a response tag.
        "created": result.findtext("creation_time"),
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
    # NVTs are loaded with the same lastupdated/instance scoping as results
    # (see load_results_and_nvts) but were never cleaned up here, so NVTs no
    # longer detected in any current result (patched, or aged out of the
    # lookback window) would accumulate forever instead of being removed.
    logger.debug("Running OpenVAS NVT cleanup job")
    GraphJob.from_node_schema(
        OpenVASNVTSchema(),
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
