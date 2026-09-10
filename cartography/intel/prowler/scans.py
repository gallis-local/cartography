import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.prowler import api
from cartography.intel.prowler.relationships import related_id
from cartography.intel.prowler.response import optional_nonempty_string
from cartography.intel.prowler.response import optional_number
from cartography.intel.prowler.response import parse_datetime
from cartography.intel.prowler.response import require_nonempty_string
from cartography.intel.prowler.response import require_object
from cartography.models.prowler import ProwlerScanSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    session: requests.Session,
    api_url: str,
    credential: api.ProwlerCredential,
) -> list[dict[str, Any]]:
    """Fetch every scan recorded in the Prowler tenant."""
    return list(
        api.iter_resources(
            session,
            api_url,
            credential,
            api.SCANS_PATH,
            result_name="scans",
        ),
    )


def transform(raw_scans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape Prowler scan objects for ingest."""
    transformed: list[dict[str, Any]] = []
    for raw_scan in raw_scans:
        scan_id = require_nonempty_string(raw_scan.get("id"), "Prowler scan id")
        attributes = require_object(
            raw_scan.get("attributes"),
            "Prowler scan attributes",
        )
        transformed.append(
            {
                "id": scan_id,
                "name": optional_nonempty_string(
                    attributes.get("name"),
                    "Prowler scan.name",
                ),
                "trigger": optional_nonempty_string(
                    attributes.get("trigger"),
                    "Prowler scan.trigger",
                ),
                "state": optional_nonempty_string(
                    attributes.get("state"),
                    "Prowler scan.state",
                ),
                "unique_resource_count": optional_number(
                    attributes.get("unique_resource_count"),
                    "Prowler scan.unique_resource_count",
                ),
                "progress": optional_number(
                    attributes.get("progress"),
                    "Prowler scan.progress",
                ),
                "duration": optional_number(
                    attributes.get("duration"),
                    "Prowler scan.duration",
                ),
                "provider_id": related_id(raw_scan, "provider", "Prowler scan"),
                "inserted_at": parse_datetime(
                    attributes.get("inserted_at"),
                    "Prowler scan.inserted_at",
                ),
                "started_at": parse_datetime(
                    attributes.get("started_at"),
                    "Prowler scan.started_at",
                ),
                "completed_at": parse_datetime(
                    attributes.get("completed_at"),
                    "Prowler scan.completed_at",
                ),
                "scheduled_at": parse_datetime(
                    attributes.get("scheduled_at"),
                    "Prowler scan.scheduled_at",
                ),
                "next_scan_at": parse_datetime(
                    attributes.get("next_scan_at"),
                    "Prowler scan.next_scan_at",
                ),
            },
        )
    return transformed


def load_scans(
    neo4j_session: neo4j.Session,
    scans: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ProwlerScanSchema(),
        scans,
        lastupdated=update_tag,
        PROWLER_TENANT_ID=tenant_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    credential: api.ProwlerCredential,
    tenant_id: str,
    update_tag: int,
) -> None:
    scans = transform(get(session, api_url, credential))
    load_scans(neo4j_session, scans, tenant_id, update_tag)


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(ProwlerScanSchema(), common_job_parameters).run(
        neo4j_session,
    )
