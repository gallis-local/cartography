import logging

import neo4j
import requests

import cartography.intel.fleetdm.fleets
import cartography.intel.fleetdm.hosts
import cartography.intel.fleetdm.labels
import cartography.intel.fleetdm.policies
import cartography.intel.fleetdm.software
import cartography.intel.fleetdm.tenant
import cartography.intel.fleetdm.users
import cartography.intel.fleetdm.versions
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)


@timeit
def start_fleetdm_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.fleetdm_base_url or not config.fleetdm_api_token:
        logger.info(
            "FleetDM import is not configured - skipping this module. "
            "Set FLEETDM_BASE_URL and FLEETDM_API_TOKEN.",
        )
        return

    api_session = requests.Session()
    api_session.headers.update(
        {
            "Authorization": f"Bearer {config.fleetdm_api_token}",
            "Content-Type": "application/json",
        }
    )

    base_url = config.fleetdm_base_url.rstrip("/")
    tenant_id = base_url

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": tenant_id,
    }

    cartography.intel.fleetdm.tenant.sync(
        neo4j_session,
        base_url,
        config.update_tag,
    )
    cartography.intel.fleetdm.fleets.sync(
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.fleetdm.hosts.sync(
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.fleetdm.software.sync(
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.fleetdm.versions.sync(
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.fleetdm.policies.sync(
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.fleetdm.users.sync(
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.fleetdm.labels.sync(
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
