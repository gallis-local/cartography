import asyncio
import logging

import neo4j

import cartography.intel.unifi.clients
import cartography.intel.unifi.devices
import cartography.intel.unifi.dpi_apps
import cartography.intel.unifi.dpi_groups
import cartography.intel.unifi.firewall_policies
import cartography.intel.unifi.firewall_zones
import cartography.intel.unifi.port_forwards
import cartography.intel.unifi.ports
import cartography.intel.unifi.sites
import cartography.intel.unifi.system_info
import cartography.intel.unifi.traffic_routes
import cartography.intel.unifi.traffic_rules
import cartography.intel.unifi.vouchers
import cartography.intel.unifi.wlans
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
    verify_ssl: bool,
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
    :param verify_ssl: Whether to verify SSL certificates
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
            verify_ssl=verify_ssl,
        )

        common_job_parameters = {
            "UPDATE_TAG": update_tag,
        }

        # Get the site ID from the controller config
        await controller.sites.update()
        site_id = controller.connectivity.config.site

        # Sync in hierarchical order:
        # 1. Sites (top level organization)
        await cartography.intel.unifi.sites.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 2. Devices (belong to sites)
        await cartography.intel.unifi.devices.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 3. WLANs (belong to sites, broadcast by devices)
        await cartography.intel.unifi.wlans.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        # 4. Ports (belong to devices)
        await cartography.intel.unifi.ports.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 5. Clients (connect to devices and WLANs)
        await cartography.intel.unifi.clients.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 6. Network configuration objects
        # Port forwards
        await cartography.intel.unifi.port_forwards.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        # Traffic rules
        await cartography.intel.unifi.traffic_rules.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        # Traffic routes
        await cartography.intel.unifi.traffic_routes.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        # 7. DPI (Deep Packet Inspection) objects
        # Apps must come before groups: UnifiDPIGroupSchema creates CONTAINS_APP
        # edges via OPTIONAL MATCH on UnifiDPIApp nodes, so app nodes must already
        # exist when groups are loaded or the relationship silently does not form.
        await cartography.intel.unifi.dpi_apps.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        await cartography.intel.unifi.dpi_groups.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        # 8. Firewall zones (must come before policies; policies reference zone IDs)
        await cartography.intel.unifi.firewall_zones.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        # 9. Firewall policies (depend on firewall zones existing)
        await cartography.intel.unifi.firewall_policies.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        # 10. System information (controller metadata)
        await cartography.intel.unifi.system_info.sync(
            neo4j_session,
            controller,
            site_id,
            common_job_parameters,
        )

        # 11. Vouchers (guest network access codes)
        await cartography.intel.unifi.vouchers.sync(
            neo4j_session,
            controller,
            site_id,
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
            verify_ssl=config.unifi_verify_ssl,
            update_tag=config.update_tag,
        )
    )
