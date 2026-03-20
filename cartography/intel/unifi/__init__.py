import asyncio
import logging

import neo4j

import cartography.intel.unifi.admins
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
    site: str | None,
    port: int,
    verify_ssl: bool,
    update_tag: int,
) -> None:
    """
    Async function to sync UniFi data for a single site.

    :param neo4j_session: Neo4j session
    :param host: UniFi controller host
    :param username: UniFi controller username
    :param password: UniFi controller password
    :param site: UniFi site name (URL slug, e.g. 'default'). Defaults to 'default' if None.
    :param port: UniFi controller port
    :param verify_ssl: Whether to verify SSL certificates
    :param update_tag: Update tag for tracking data freshness
    """
    # Default to 'default' if no site is configured — passing None to aiounifi
    # would produce URLs like /api/s/None/... causing 401s.
    site = site or "default"

    controller = None
    try:
        controller = await create_unifi_controller(
            host=host,
            username=username,
            password=password,
            site=site,
            port=port,
            verify_ssl=verify_ssl,
        )

        # Look up the site's MongoDB _id so that all RESOURCE relationships
        # to UnifiSite nodes use the same ID value as the stored site nodes.
        await controller.sites.update()
        config_site_name = controller.connectivity.config.site
        site_id = next(
            (s.site_id for s in controller.sites.values() if s.name == config_site_name),
            config_site_name,  # fallback: use slug if no match (should not happen)
        )

        common_job_parameters = {
            "UPDATE_TAG": update_tag,
            "site_id": site_id,
        }

        # Sync in hierarchical order. Each module is wrapped in try/except
        # so that a failure in one module does not block the rest of the sync.
        failed_modules: list[str] = []

        # 1. Sites (top level organization) — required by all other modules
        try:
            await cartography.intel.unifi.sites.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi sites — aborting remaining modules.")
            raise

        # 2. WLANs — must come BEFORE devices so BROADCASTS relationships resolve on first run
        try:
            await cartography.intel.unifi.wlans.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi WLANs.")
            failed_modules.append("wlans")

        # 3. Devices (belong to sites, reference WLANs via BROADCASTS)
        try:
            await cartography.intel.unifi.devices.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi devices.")
            failed_modules.append("devices")

        # 4. Ports (belong to devices)
        if "devices" not in failed_modules:
            try:
                await cartography.intel.unifi.ports.sync(
                    neo4j_session,
                    controller,
                    common_job_parameters,
                )
            except Exception:
                logger.exception("Failed to sync UniFi ports.")
                failed_modules.append("ports")
        else:
            logger.warning("Skipping UniFi ports sync because devices sync failed.")

        # 5. Clients (connect to devices and WLANs)
        if "devices" not in failed_modules:
            try:
                await cartography.intel.unifi.clients.sync(
                    neo4j_session,
                    controller,
                    common_job_parameters,
                )
            except Exception:
                logger.exception("Failed to sync UniFi clients.")
                failed_modules.append("clients")
        else:
            logger.warning("Skipping UniFi clients sync because devices sync failed.")

        # 6. Port forwards
        try:
            await cartography.intel.unifi.port_forwards.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi port forwards.")
            failed_modules.append("port_forwards")

        # 7. Traffic rules
        try:
            await cartography.intel.unifi.traffic_rules.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi traffic rules.")
            failed_modules.append("traffic_rules")

        # 8. Traffic routes
        try:
            await cartography.intel.unifi.traffic_routes.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi traffic routes.")
            failed_modules.append("traffic_routes")

        # 9. DPI apps — must come BEFORE DPI groups (groups reference app IDs)
        try:
            await cartography.intel.unifi.dpi_apps.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi DPI apps.")
            failed_modules.append("dpi_apps")

        # 10. DPI groups (depend on DPI apps)
        if "dpi_apps" not in failed_modules:
            try:
                await cartography.intel.unifi.dpi_groups.sync(
                    neo4j_session,
                    controller,
                    common_job_parameters,
                )
            except Exception:
                logger.exception("Failed to sync UniFi DPI groups.")
                failed_modules.append("dpi_groups")
        else:
            logger.warning("Skipping UniFi DPI groups sync because DPI apps sync failed.")

        # 11. Firewall zones — must come BEFORE firewall policies
        try:
            await cartography.intel.unifi.firewall_zones.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi firewall zones.")
            failed_modules.append("firewall_zones")

        # 12. Firewall policies (depend on firewall zones)
        if "firewall_zones" not in failed_modules:
            try:
                await cartography.intel.unifi.firewall_policies.sync(
                    neo4j_session,
                    controller,
                    common_job_parameters,
                )
            except Exception:
                logger.exception("Failed to sync UniFi firewall policies.")
                failed_modules.append("firewall_policies")
        else:
            logger.warning(
                "Skipping UniFi firewall policies sync because firewall zones sync failed.",
            )

        # 13. System information
        try:
            await cartography.intel.unifi.system_info.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi system info.")
            failed_modules.append("system_info")

        # 14. Vouchers
        try:
            await cartography.intel.unifi.vouchers.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi vouchers.")
            failed_modules.append("vouchers")

        # 15. Admins — last; requires super-admin privileges and failure must not
        # break the session for other modules (aiounifi retries on 401 => 429 lockout)
        try:
            await cartography.intel.unifi.admins.sync(
                neo4j_session,
                controller,
                common_job_parameters,
            )
        except Exception:
            logger.exception("Failed to sync UniFi admins.")
            failed_modules.append("admins")

        if failed_modules:
            logger.error(
                "UniFi sync completed with failures in: %s",
                ", ".join(failed_modules),
            )

    finally:
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
