import logging
from typing import Any

import neo4j

import cartography.intel.prowler.findings
import cartography.intel.prowler.providers
import cartography.intel.prowler.resources
import cartography.intel.prowler.scans
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.prowler import api
from cartography.intel.prowler.response import optional_nonempty_string
from cartography.intel.prowler.response import parse_datetime
from cartography.intel.prowler.response import require_nonempty_string
from cartography.intel.prowler.response import require_object
from cartography.models.prowler import ProwlerTenantSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _build_credential(
    session: Any,
    config: Config,
    api_url: str,
) -> api.ProwlerCredential:
    """Build a Prowler credential from an API key, or from email and password."""
    if config.prowler_api_key:
        credential = api.ProwlerCredential(api_url, api_key=config.prowler_api_key)
        credential.apply(session)
        return credential

    logger.debug("No Prowler API key configured, authenticating with email/password.")
    return api.authenticate_with_password(
        session,
        api_url,
        config.prowler_email,
        config.prowler_password,
        config.prowler_tenant_id,
    )


def _resolve_tenant(
    session: Any,
    api_url: str,
    credential: api.ProwlerCredential,
    configured_tenant_id: str | None,
) -> dict[str, Any]:
    """Return the tenant to sync, honouring an explicitly configured tenant id."""
    tenants = api.get_tenants(session, api_url, credential)
    if not tenants:
        raise RuntimeError("Prowler credential has access to no tenants")

    if configured_tenant_id:
        matches = [
            tenant for tenant in tenants if tenant.get("id") == configured_tenant_id
        ]
        if not matches:
            raise RuntimeError(
                f"Prowler credential has no access to tenant {configured_tenant_id}",
            )
        selected = matches[0]
    else:
        if len(tenants) > 1:
            logger.warning(
                "Prowler credential has access to %d tenants and none was configured. "
                "Syncing the first one. Set --prowler-tenant-id to choose explicitly.",
                len(tenants),
            )
        selected = tenants[0]

    attributes = require_object(
        selected.get("attributes"),
        "Prowler tenant attributes",
    )
    return {
        "id": require_nonempty_string(selected.get("id"), "Prowler tenant id"),
        "name": optional_nonempty_string(
            attributes.get("name"),
            "Prowler tenant.name",
        ),
        "api_url": api_url,
        "inserted_at": parse_datetime(
            attributes.get("inserted_at"),
            "Prowler tenant.inserted_at",
        ),
        "updated_at": parse_datetime(
            attributes.get("updated_at"),
            "Prowler tenant.updated_at",
        ),
    }


@timeit
def start_prowler_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """Ingest Prowler providers, scans, resources, and security findings."""
    api_url = config.prowler_api_url
    has_api_key = bool(config.prowler_api_key)
    has_password = bool(config.prowler_email and config.prowler_password)
    if not api_url or not (has_api_key or has_password):
        logger.info(
            "Prowler import is not configured - skipping this module. "
            "Set prowler_api_url and either prowler_api_key or "
            "prowler_email/prowler_password to enable.",
        )
        return

    try:
        api_url = api.normalize_api_url(api_url)
    except ValueError as exc:
        logger.warning("Invalid Prowler API URL - skipping this module: %s", exc)
        return

    session = api.create_session()
    try:
        credential = _build_credential(session, config, api_url)
        tenant = _resolve_tenant(
            session,
            api_url,
            credential,
            config.prowler_tenant_id,
        )
        tenant_id = tenant["id"]
        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "PROWLER_TENANT_ID": tenant_id,
        }

        load(
            neo4j_session,
            ProwlerTenantSchema(),
            [tenant],
            lastupdated=config.update_tag,
        )

        # Providers load first so scans and resources have something to attach to.
        cartography.intel.prowler.providers.sync(
            neo4j_session,
            session,
            api_url,
            credential,
            tenant_id,
            config.update_tag,
        )
        cartography.intel.prowler.scans.sync(
            neo4j_session,
            session,
            api_url,
            credential,
            tenant_id,
            config.update_tag,
        )
        cartography.intel.prowler.resources.sync(
            neo4j_session,
            session,
            api_url,
            credential,
            tenant_id,
            config.update_tag,
        )
        cartography.intel.prowler.findings.sync(
            neo4j_session,
            session,
            api_url,
            credential,
            tenant_id,
            config.update_tag,
        )

        # Cleanup is deliberately deferred until every feed has completed, so a
        # mid-sync failure leaves the last known good graph in place.
        cartography.intel.prowler.findings.cleanup(
            neo4j_session,
            common_job_parameters,
        )
        cartography.intel.prowler.resources.cleanup(
            neo4j_session,
            common_job_parameters,
        )
        cartography.intel.prowler.scans.cleanup(neo4j_session, common_job_parameters)
        cartography.intel.prowler.providers.cleanup(
            neo4j_session,
            common_job_parameters,
        )

        merge_module_sync_metadata(
            neo4j_session,
            group_type="ProwlerTenant",
            group_id=tenant_id,
            synced_type="ProwlerData",
            update_tag=config.update_tag,
            stat_handler=stat_handler,
        )
    finally:
        session.close()
