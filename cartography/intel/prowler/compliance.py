import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.prowler import api
from cartography.intel.prowler.response import optional_nonempty_string
from cartography.intel.prowler.response import optional_number
from cartography.intel.prowler.response import require_nonempty_string
from cartography.intel.prowler.response import require_object
from cartography.models.prowler import ProwlerComplianceAssessmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    session: requests.Session,
    api_url: str,
    credential: api.ProwlerCredential,
    provider_ids: list[str],
) -> list[dict[str, Any]]:
    """Fetch each provider's compliance posture.

    The compliance overview objects carry no relationship back to their
    provider, so this issues one request per provider and pairs the results with
    the provider id that produced them. Filtering by provider also makes the API
    report against that provider's latest completed scan.
    """
    results: list[dict[str, Any]] = []
    for provider_id in provider_ids:
        for raw in api.iter_resources(
            session,
            api_url,
            credential,
            api.COMPLIANCE_PATH,
            params={"filter[provider_id]": provider_id},
            result_name="compliance overviews",
        ):
            results.append({"provider_id": provider_id, "overview": raw})
    return results


def transform(raw_overviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape Prowler compliance overview objects for ingest."""
    transformed: list[dict[str, Any]] = []
    for entry in raw_overviews:
        provider_id = entry["provider_id"]
        raw_overview = require_object(entry["overview"], "Prowler compliance overview")
        attributes = require_object(
            raw_overview.get("attributes"),
            "Prowler compliance overview attributes",
        )
        compliance_id = require_nonempty_string(
            attributes.get("id"),
            "Prowler compliance overview.id",
        )
        transformed.append(
            {
                # The same framework is assessed once per provider, so the node
                # identity has to carry the provider too.
                "id": f"{provider_id}:{compliance_id}",
                "compliance_id": compliance_id,
                "framework": optional_nonempty_string(
                    attributes.get("framework"),
                    "Prowler compliance overview.framework",
                ),
                "version": optional_nonempty_string(
                    attributes.get("version"),
                    "Prowler compliance overview.version",
                ),
                "requirements_passed": optional_number(
                    attributes.get("requirements_passed"),
                    "Prowler compliance overview.requirements_passed",
                ),
                "requirements_failed": optional_number(
                    attributes.get("requirements_failed"),
                    "Prowler compliance overview.requirements_failed",
                ),
                "requirements_manual": optional_number(
                    attributes.get("requirements_manual"),
                    "Prowler compliance overview.requirements_manual",
                ),
                "total_requirements": optional_number(
                    attributes.get("total_requirements"),
                    "Prowler compliance overview.total_requirements",
                ),
                "provider_id": provider_id,
            },
        )
    return transformed


def load_compliance_assessments(
    neo4j_session: neo4j.Session,
    assessments: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ProwlerComplianceAssessmentSchema(),
        assessments,
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
    provider_ids: list[str],
    update_tag: int,
) -> None:
    assessments = transform(get(session, api_url, credential, provider_ids))
    load_compliance_assessments(neo4j_session, assessments, tenant_id, update_tag)


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        ProwlerComplianceAssessmentSchema(),
        common_job_parameters,
    ).run(neo4j_session)
