import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.prowler import api
from cartography.intel.prowler.relationships import index_included
from cartography.intel.prowler.relationships import related_id
from cartography.intel.prowler.relationships import related_ids
from cartography.intel.prowler.response import canonical_cve_ids
from cartography.intel.prowler.response import optional_bool
from cartography.intel.prowler.response import optional_nonempty_string
from cartography.intel.prowler.response import optional_object
from cartography.intel.prowler.response import optional_string_list
from cartography.intel.prowler.response import parse_datetime
from cartography.intel.prowler.response import require_nonempty_string
from cartography.intel.prowler.response import require_object
from cartography.models.prowler import ProwlerFindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Sideload the resources each finding was raised against so their provider-native
# identifiers land on the finding without an extra request per row.
_FINDINGS_PARAMS = {"include": "resources"}


def _nested(source: dict[str, Any], *keys: str) -> Any:
    """Walk a chain of nested object keys, stopping at the first missing level."""
    current: Any = source
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _check_metadata_cve_ids(metadata: dict[str, Any]) -> list[str]:
    """Return the CVE identifiers named in a check's `relatedto` and aliases.

    Most Prowler checks are configuration checks and name no CVE at all, so this
    is usually empty.
    """
    candidates: list[str] = []
    for key in ("relatedto", "checkaliases"):
        value = metadata.get(key)
        if isinstance(value, list):
            candidates.extend(item for item in value if isinstance(item, str))
    return canonical_cve_ids(candidates)


def _compliance_frameworks(metadata: dict[str, Any]) -> list[str] | None:
    """Return the sorted names of the compliance frameworks a check maps to."""
    compliance = metadata.get("compliance")
    if not isinstance(compliance, dict):
        return None
    frameworks = sorted(key for key in compliance if isinstance(key, str))
    return frameworks or None


@timeit
def get(
    session: requests.Session,
    api_url: str,
    credential: api.ProwlerCredential,
) -> list[dict[str, Any]]:
    """Fetch the current findings of the most recent scan per provider.

    Each entry pairs one page's findings with that page's sideloaded resources,
    because `included` is scoped to the document it arrived in.
    """
    pages: list[dict[str, Any]] = []
    for document in api.iter_pages(
        session,
        api_url,
        credential,
        api.FINDINGS_PATH,
        params=_FINDINGS_PARAMS,
        result_name="findings",
    ):
        pages.append(
            {
                "findings": api.page_rows(document, "findings"),
                "resources": index_included(document, "resources"),
            },
        )
    return pages


def transform(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape Prowler finding objects for ingest."""
    transformed: list[dict[str, Any]] = []
    for page in pages:
        resources_by_id = page["resources"]
        for raw_finding in page["findings"]:
            raw_finding = require_object(raw_finding, "Prowler finding")
            finding_id = require_nonempty_string(
                raw_finding.get("id"),
                "Prowler finding id",
            )
            attributes = require_object(
                raw_finding.get("attributes"),
                "Prowler finding attributes",
            )
            # check_metadata is not a required attribute, so treat its absence
            # as "no metadata" rather than failing the whole page.
            metadata = optional_object(
                attributes.get("check_metadata"),
                "Prowler finding.check_metadata",
            )

            resource_ids = related_ids(raw_finding, "resources", "Prowler finding")
            resource_uids: list[str] = []
            for resource_id in resource_ids:
                resource = resources_by_id.get(resource_id)
                if resource is None:
                    # The resource was not sideloaded on this page. The finding
                    # still links to it by id; only the ARN is unavailable here.
                    continue
                uid = optional_nonempty_string(
                    _nested(resource, "attributes", "uid"),
                    "Prowler finding.resources.uid",
                )
                if uid is not None and uid not in resource_uids:
                    resource_uids.append(uid)

            transformed.append(
                {
                    "id": finding_id,
                    "uid": require_nonempty_string(
                        attributes.get("uid"),
                        "Prowler finding.uid",
                    ),
                    "check_id": require_nonempty_string(
                        attributes.get("check_id"),
                        "Prowler finding.check_id",
                    ),
                    "check_title": optional_nonempty_string(
                        metadata.get("checktitle"),
                        "Prowler finding.check_metadata.checktitle",
                    ),
                    "description": optional_nonempty_string(
                        metadata.get("description"),
                        "Prowler finding.check_metadata.description",
                    ),
                    "status": optional_nonempty_string(
                        attributes.get("status"),
                        "Prowler finding.status",
                    ),
                    "status_extended": optional_nonempty_string(
                        attributes.get("status_extended"),
                        "Prowler finding.status_extended",
                    ),
                    "severity": require_nonempty_string(
                        attributes.get("severity"),
                        "Prowler finding.severity",
                    ),
                    "delta": optional_nonempty_string(
                        attributes.get("delta"),
                        "Prowler finding.delta",
                    ),
                    "service_name": optional_nonempty_string(
                        metadata.get("servicename"),
                        "Prowler finding.check_metadata.servicename",
                    ),
                    "resource_type": optional_nonempty_string(
                        metadata.get("resourcetype"),
                        "Prowler finding.check_metadata.resourcetype",
                    ),
                    "resource_groups": optional_nonempty_string(
                        attributes.get("resource_groups"),
                        "Prowler finding.resource_groups",
                    ),
                    "categories": optional_string_list(
                        attributes.get("categories"),
                        "Prowler finding.categories",
                    ),
                    "compliance_frameworks": _compliance_frameworks(metadata),
                    "risk": optional_nonempty_string(
                        metadata.get("risk"),
                        "Prowler finding.check_metadata.risk",
                    ),
                    "remediation_text": optional_nonempty_string(
                        _nested(metadata, "remediation", "recommendation", "text"),
                        "Prowler finding.check_metadata.remediation.recommendation.text",
                    ),
                    "remediation_url": optional_nonempty_string(
                        _nested(metadata, "remediation", "recommendation", "url"),
                        "Prowler finding.check_metadata.remediation.recommendation.url",
                    ),
                    "remediation_cli": optional_nonempty_string(
                        _nested(metadata, "remediation", "code", "cli"),
                        "Prowler finding.check_metadata.remediation.code.cli",
                    ),
                    "remediation_terraform": optional_nonempty_string(
                        _nested(metadata, "remediation", "code", "terraform"),
                        "Prowler finding.check_metadata.remediation.code.terraform",
                    ),
                    "muted": optional_bool(
                        attributes.get("muted"),
                        "Prowler finding.muted",
                    ),
                    "muted_reason": optional_nonempty_string(
                        attributes.get("muted_reason"),
                        "Prowler finding.muted_reason",
                    ),
                    "triage_status": optional_nonempty_string(
                        attributes.get("triage_status"),
                        "Prowler finding.triage_status",
                    ),
                    "cve_ids": _check_metadata_cve_ids(metadata) or None,
                    "scan_id": related_id(raw_finding, "scan", "Prowler finding"),
                    "resource_ids": resource_ids or None,
                    "resource_uids": resource_uids or None,
                    "first_seen_at": parse_datetime(
                        attributes.get("first_seen_at"),
                        "Prowler finding.first_seen_at",
                    ),
                    "inserted_at": parse_datetime(
                        attributes.get("inserted_at"),
                        "Prowler finding.inserted_at",
                    ),
                    "updated_at": parse_datetime(
                        attributes.get("updated_at"),
                        "Prowler finding.updated_at",
                    ),
                },
            )
    return transformed


def load_findings(
    neo4j_session: neo4j.Session,
    findings: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ProwlerFindingSchema(),
        findings,
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
    findings = transform(get(session, api_url, credential))
    load_findings(neo4j_session, findings, tenant_id, update_tag)
    logger.info("Loaded %d Prowler findings.", len(findings))


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(ProwlerFindingSchema(), common_job_parameters).run(
        neo4j_session,
    )
