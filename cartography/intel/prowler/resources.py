import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.prowler import api
from cartography.intel.prowler.relationships import index_included
from cartography.intel.prowler.relationships import related_id
from cartography.intel.prowler.response import optional_nonempty_string
from cartography.intel.prowler.response import optional_number
from cartography.intel.prowler.response import optional_string_list
from cartography.intel.prowler.response import parse_datetime
from cartography.intel.prowler.response import require_nonempty_string
from cartography.intel.prowler.response import require_object
from cartography.models.prowler import ProwlerResourceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Sideload each resource's provider so the transform knows which cloud the
# resource's `uid` belongs to before deciding whether it is an ARN to join on.
_RESOURCES_PARAMS = {"include": "provider"}


def _tag_lists(value: Any, field: str) -> tuple[list[str] | None, list[str] | None]:
    """Flatten a Prowler tag map into sorted key and `key=value` lists.

    Neo4j cannot store a nested map as a property, so tags are kept as two sorted
    string lists: the keys on their own, and the full `key=value` pairs.
    """
    if value is None:
        return None, None
    tags = require_object(value, field)
    keys: list[str] = []
    pairs: list[str] = []
    for key, tag_value in tags.items():
        if not isinstance(key, str):
            raise ValueError(f"{field} keys must be strings")
        if tag_value is not None and not isinstance(tag_value, (str, int, float, bool)):
            raise ValueError(f"{field}.{key} must be a scalar")
        keys.append(key)
        pairs.append(f"{key}={'' if tag_value is None else tag_value}")
    if not keys:
        return None, None
    return sorted(keys), sorted(pairs)


@timeit
def get(
    session: requests.Session,
    api_url: str,
    credential: api.ProwlerCredential,
) -> list[dict[str, Any]]:
    """Fetch the current state of every resource Prowler most recently scanned.

    Each entry pairs one page's resources with that page's sideloaded providers,
    because `included` is scoped to the document it arrived in. The provider is
    needed to know which cloud a resource's `uid` belongs to.
    """
    pages: list[dict[str, Any]] = []
    for document in api.iter_pages(
        session,
        api_url,
        credential,
        api.RESOURCES_PATH,
        params=_RESOURCES_PARAMS,
        result_name="resources",
    ):
        pages.append(
            {
                "resources": api.page_rows(document, "resources"),
                "providers": index_included(document, "providers"),
            },
        )
    return pages


def _aws_uid(
    uid: str,
    provider_type: str | None,
) -> str | None:
    """Return the resource `uid` only when it is an AWS ARN.

    The AWS correlation edges match this against an indexed `arn`. Leaving it
    None for every other provider keeps those matchers from firing at all, since
    a null matcher value resolves to no target node.
    """
    if provider_type != "aws":
        return None
    if not uid.startswith("arn:"):
        # Prowler emits a non-ARN uid for a few AWS pseudo-resources, such as an
        # account-level check target. There is nothing to join those to.
        return None
    return uid


def transform(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape Prowler resource objects for ingest."""
    transformed: list[dict[str, Any]] = []
    for page in pages:
        providers_by_id = page["providers"]
        for raw_resource in page["resources"]:
            resource_id = require_nonempty_string(
                raw_resource.get("id"),
                "Prowler resource id",
            )
            attributes = require_object(
                raw_resource.get("attributes"),
                "Prowler resource attributes",
            )
            tag_keys, tags = _tag_lists(attributes.get("tags"), "Prowler resource.tags")
            uid = require_nonempty_string(
                attributes.get("uid"),
                "Prowler resource.uid",
            )
            provider_id = related_id(
                raw_resource,
                "provider",
                "Prowler resource",
            )
            provider = providers_by_id.get(provider_id) if provider_id else None
            provider_type = None
            if provider is not None:
                provider_attributes = require_object(
                    provider.get("attributes"),
                    "Prowler resource.provider attributes",
                )
                provider_type = optional_nonempty_string(
                    provider_attributes.get("provider"),
                    "Prowler resource.provider.provider",
                )

            transformed.append(
                {
                    "id": resource_id,
                    "uid": uid,
                    "aws_uid": _aws_uid(uid, provider_type),
                    "name": optional_nonempty_string(
                        attributes.get("name"),
                        "Prowler resource.name",
                    ),
                    "region": optional_nonempty_string(
                        attributes.get("region"),
                        "Prowler resource.region",
                    ),
                    "service": optional_nonempty_string(
                        attributes.get("service"),
                        "Prowler resource.service",
                    ),
                    "resource_type": optional_nonempty_string(
                        attributes.get("type"),
                        "Prowler resource.type",
                    ),
                    "partition": optional_nonempty_string(
                        attributes.get("partition"),
                        "Prowler resource.partition",
                    ),
                    "groups": optional_string_list(
                        attributes.get("groups"),
                        "Prowler resource.groups",
                    ),
                    "failed_findings_count": optional_number(
                        attributes.get("failed_findings_count"),
                        "Prowler resource.failed_findings_count",
                    ),
                    "tag_keys": tag_keys,
                    "tags": tags,
                    "provider_id": provider_id,
                    "inserted_at": parse_datetime(
                        attributes.get("inserted_at"),
                        "Prowler resource.inserted_at",
                    ),
                    "updated_at": parse_datetime(
                        attributes.get("updated_at"),
                        "Prowler resource.updated_at",
                    ),
                },
            )
    return transformed


def load_resources(
    neo4j_session: neo4j.Session,
    resources: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ProwlerResourceSchema(),
        resources,
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
    resources = transform(get(session, api_url, credential))
    load_resources(neo4j_session, resources, tenant_id, update_tag)


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(ProwlerResourceSchema(), common_job_parameters).run(
        neo4j_session,
    )
