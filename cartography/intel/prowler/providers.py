import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.prowler import api
from cartography.intel.prowler.response import optional_bool
from cartography.intel.prowler.response import optional_nonempty_string
from cartography.intel.prowler.response import parse_datetime
from cartography.intel.prowler.response import require_nonempty_string
from cartography.intel.prowler.response import require_object
from cartography.models.prowler import ProwlerProviderSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Prowler provider types whose `uid` is the same identifier Cartography uses for
# the corresponding cloud tenant node, keyed by the transform field that carries
# it. Types absent from this map are still ingested; they just do not get an edge
# to a cloud node.
_CLOUD_ACCOUNT_FIELDS = {
    "aws": "aws_account_id",
    "azure": "azure_subscription_id",
    "gcp": "gcp_project_id",
    "kubernetes": "kubernetes_cluster_name",
    "github": "github_organization_login",
}
_ALL_CLOUD_ACCOUNT_FIELDS = tuple(_CLOUD_ACCOUNT_FIELDS.values())


@timeit
def get(
    session: requests.Session,
    api_url: str,
    credential: api.ProwlerCredential,
) -> list[dict[str, Any]]:
    """Fetch every provider configured in the Prowler tenant."""
    return list(
        api.iter_resources(
            session,
            api_url,
            credential,
            api.PROVIDERS_PATH,
            result_name="providers",
        ),
    )


def transform(raw_providers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape Prowler provider objects for ingest."""
    transformed: list[dict[str, Any]] = []
    for raw_provider in raw_providers:
        provider_id = require_nonempty_string(
            raw_provider.get("id"), "Prowler provider id"
        )
        attributes = require_object(
            raw_provider.get("attributes"),
            "Prowler provider attributes",
        )
        provider_type = require_nonempty_string(
            attributes.get("provider"),
            "Prowler provider.provider",
        )
        uid = require_nonempty_string(attributes.get("uid"), "Prowler provider.uid")

        connection = attributes.get("connection")
        connected = None
        last_checked_at = None
        if connection is not None:
            connection = require_object(connection, "Prowler provider.connection")
            connected = optional_bool(
                connection.get("connected"),
                "Prowler provider.connection.connected",
            )
            last_checked_at = parse_datetime(
                connection.get("last_checked_at"),
                "Prowler provider.connection.last_checked_at",
            )

        provider = {
            "id": provider_id,
            "uid": uid,
            "provider_type": provider_type,
            "alias": optional_nonempty_string(
                attributes.get("alias"),
                "Prowler provider.alias",
            ),
            "available": optional_bool(
                attributes.get("available"),
                "Prowler provider.available",
            ),
            "connected": connected,
            "connection_last_checked_at": last_checked_at,
            "is_dynamic": optional_bool(
                attributes.get("is_dynamic"),
                "Prowler provider.is_dynamic",
            ),
            "is_imported": optional_bool(
                attributes.get("is_imported"),
                "Prowler provider.is_imported",
            ),
            "inserted_at": parse_datetime(
                attributes.get("inserted_at"),
                "Prowler provider.inserted_at",
            ),
            "updated_at": parse_datetime(
                attributes.get("updated_at"),
                "Prowler provider.updated_at",
            ),
        }
        # Only the field matching this provider's type is populated. The others
        # stay None so their relationship matchers find nothing, which is how a
        # single schema links four different kinds of cloud tenant node.
        for field in _ALL_CLOUD_ACCOUNT_FIELDS:
            provider[field] = None
        cloud_account_field = _CLOUD_ACCOUNT_FIELDS.get(provider_type)
        if cloud_account_field is not None:
            provider[cloud_account_field] = uid

        transformed.append(provider)
    return transformed


def load_providers(
    neo4j_session: neo4j.Session,
    providers: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ProwlerProviderSchema(),
        providers,
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
) -> list[str]:
    """Sync Prowler providers, returning their ids for the compliance sync."""
    providers = transform(get(session, api_url, credential))
    load_providers(neo4j_session, providers, tenant_id, update_tag)
    return [provider["id"] for provider in providers]


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(ProwlerProviderSchema(), common_job_parameters).run(
        neo4j_session,
    )
