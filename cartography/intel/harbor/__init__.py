import logging

import neo4j

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.harbor import artifacts
from cartography.intel.harbor import projects
from cartography.intel.harbor import repositories
from cartography.intel.harbor import sbom
from cartography.intel.harbor import vulnerabilities
from cartography.intel.harbor.util import create_session
from cartography.intel.harbor.util import get_json
from cartography.intel.harbor.util import normalize_base_url
from cartography.models.harbor.tenant import HarborInstanceSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_harbor_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Ingest the projects, repositories, images, tags, vulnerabilities, and SBOM
    packages of a Harbor registry.
    """
    if (
        not config.harbor_url
        or not config.harbor_username
        or not config.harbor_password
    ):
        logger.info(
            "Harbor import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    base_url, instance_id = normalize_base_url(config.harbor_url)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "INSTANCE_ID": instance_id,
    }
    logger.info("Starting Harbor ingestion for %s", instance_id)
    with create_session(
        config.harbor_username,
        config.harbor_password,
        config.harbor_verify_ssl,
    ) as session:
        system_info = get_json(session, base_url, "/systeminfo")
        load(
            neo4j_session,
            HarborInstanceSchema(),
            [
                {
                    "id": instance_id,
                    "url": base_url,
                    "version": system_info.get("harbor_version"),
                }
            ],
            lastupdated=config.update_tag,
        )
        synced_projects = projects.sync(
            neo4j_session,
            session,
            base_url,
            instance_id,
            config.update_tag,
            common_job_parameters,
        )
        synced_repositories = repositories.sync(
            neo4j_session,
            session,
            base_url,
            instance_id,
            synced_projects,
            config.update_tag,
            common_job_parameters,
        )
        synced_images = artifacts.sync(
            neo4j_session,
            session,
            base_url,
            instance_id,
            synced_repositories,
            config.update_tag,
            common_job_parameters,
        )
        # Packages load before vulnerabilities so each finding's AFFECTS edge to
        # its package resolves on the first sync.
        sbom.sync(
            neo4j_session,
            session,
            base_url,
            instance_id,
            synced_images,
            config.update_tag,
            common_job_parameters,
        )
        vulnerabilities.sync(
            neo4j_session,
            session,
            base_url,
            instance_id,
            synced_images,
            config.update_tag,
            common_job_parameters,
        )
    merge_module_sync_metadata(
        neo4j_session,
        group_type="HarborInstance",
        group_id=instance_id,
        synced_type="HarborData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
    logger.info("Completed Harbor ingestion for %s", instance_id)
