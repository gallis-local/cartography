import asyncio
import logging

import neo4j

import cartography.intel.unifi.clients
import cartography.intel.unifi.devices
from cartography.config import Config
from cartography.intel.unifi.util import close_controller
from cartography.intel.unifi.util import create_unifi_controller
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def _sync_unifi(
    neo4j_session: neo4j.Session,
    host: str,
    username: str,
    password: str,
    site: str,
    port: int,
    update_tag: int,
) -> None:
    """
    Async function to sync UniFi data.

    :param neo4j_session: Neo4j session
    :param host: UniFi controller host
    :param username: UniFi controller username
    :param password: UniFi controller password
    :param site: UniFi site name
    :param port: UniFi controller port
    :param update_tag: Update tag for tracking data freshness
    """
    controller = None
    try:
        # Create and connect to UniFi controller
        controller = await create_unifi_controller(
            host=host,
            username=username,
            password=password,
            site=site,
            port=port,
        )

        common_job_parameters = {
            "UPDATE_TAG": update_tag,
        }

        # Sync devices first, then clients (since clients reference devices)
        await cartography.intel.unifi.devices.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        await cartography.intel.unifi.clients.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

    finally:
        # Always close the controller connection
        if controller:
            await close_controller(controller)


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

    # Run async sync using asyncio.run()
    asyncio.run(
        _sync_unifi(
            neo4j_session=neo4j_session,
            host=config.unifi_host,
            username=config.unifi_user,
            password=config.unifi_password,
            site=config.unifi_site,
            port=config.unifi_port,
            update_tag=config.update_tag,
        )
    )
