import logging

import neo4j

import cartography.intel.unifi.clients
import cartography.intel.unifi.devices
from cartography.config import Config
from cartography.intel.unifi.util import get_unifi_client
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_unifi_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of UniFi data. Otherwise warn and exit.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.unifi_host:
        logger.info(
            "UniFi import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    if not config.unifi_user or not config.unifi_password:
        logger.warning(
            "UniFi credentials not configured - skipping this module. "
            "Please provide --unifi-user and --unifi-password-env-var.",
        )
        return

    # Create UniFi client
    client = get_unifi_client(
        host=config.unifi_host,
        username=config.unifi_user,
        password=config.unifi_password,
        site=config.unifi_site,
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Sync devices first, then clients (since clients reference devices)
    cartography.intel.unifi.devices.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    cartography.intel.unifi.clients.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )
