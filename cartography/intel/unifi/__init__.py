import asyncio
import logging
from typing import Any

import neo4j

import cartography.intel.unifi.admins
import cartography.intel.unifi.clients
import cartography.intel.unifi.clients_all
import cartography.intel.unifi.devices
import cartography.intel.unifi.dpi_apps
import cartography.intel.unifi.dpi_groups
import cartography.intel.unifi.firewall_policies
import cartography.intel.unifi.firewall_zones
import cartography.intel.unifi.network_configs
import cartography.intel.unifi.outlets
import cartography.intel.unifi.port_forwards
import cartography.intel.unifi.ports
import cartography.intel.unifi.sites
import cartography.intel.unifi.speedtests
import cartography.intel.unifi.system_info
import cartography.intel.unifi.traffic_routes
import cartography.intel.unifi.traffic_rules
import cartography.intel.unifi.vouchers
import cartography.intel.unifi.wlans
from cartography.config import Config
from cartography.intel.unifi.util import close_controller
from cartography.intel.unifi.util import create_unifi_controller
from cartography.util import merge_module_sync_metadata
from cartography.util import run_analysis_and_ensure_deps
from cartography.util import timeit
from cartography.stats import get_stats_client

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# Module sync order - matches the order in _sync_unifi()
# This defines dependencies between modules
UNIFI_MODULE_DEPENDENCIES = {
    "wlans": ["sites"],
    "devices": ["sites", "wlans"],
    "ports": ["sites", "devices"],
    "clients": ["sites", "devices", "wlans", "ports"],
    "clients_all": ["sites", "devices", "wlans", "ports"],
    "port_forwards": ["sites"],
    "traffic_rules": ["sites"],
    "traffic_routes": ["sites"],
    "dpi_apps": ["sites"],
    "dpi_groups": ["sites", "dpi_apps"],
    "firewall_zones": ["sites"],
    "firewall_policies": ["sites", "firewall_zones"],
    "system_info": ["sites"],
    "vouchers": ["sites"],
    "admins": ["sites"],
    "network_configs": ["sites", "firewall_zones"],
    "outlets": ["sites", "devices"],
    "speedtests": ["sites", "devices"],
}

# Analysis job requirements - which modules must be synced before running each analysis
UNIFI_ANALYSIS_REQUIREMENTS = {
    "unifi_internet_exposure.json": {
        "port_forwards",
        "devices",
        "wlans",
        "firewall_zones",
        "firewall_policies",
    },
    "unifi_firmware_compliance.json": {"devices"},
    "unifi_guest_isolation.json": {
        "wlans",
        "firewall_policies",
        "firewall_zones",
        "vouchers",
        "clients",
    },
    "unifi_device_health.json": {"devices"},
    "unifi_network_config_audit.json": {"network_configs"},
    "unifi_power_monitoring.json": {"outlets"},
    "unifi_wan_performance.json": {"speedtests"},
}


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
    logger.info("Starting UniFi ingestion for host %s, site %s", host, site)

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
            (
                s.site_id
                for s in controller.sites.values()
                if s.name == config_site_name
            ),
            config_site_name,  # fallback: use slug if no match (should not happen)
        )

        common_job_parameters = {
            "UPDATE_TAG": update_tag,
            "site_id": site_id,
        }

        # Sync in hierarchical order.
        # 1. Sites (top level organization) — required by all other modules
        await cartography.intel.unifi.sites.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 2. WLANs — must come BEFORE devices so BROADCASTS relationships resolve on first run
        await cartography.intel.unifi.wlans.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 3. Devices (belong to sites, reference WLANs via BROADCASTS)
        await cartography.intel.unifi.devices.sync(
            neo4j_session,
            controller,
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

        # 6. Historical clients (depends on devices for ap_switch_mac)
        await cartography.intel.unifi.clients_all.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 7. Port forwards
        await cartography.intel.unifi.port_forwards.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 8. Traffic rules
        await cartography.intel.unifi.traffic_rules.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 9. Traffic routes
        await cartography.intel.unifi.traffic_routes.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 10. DPI apps — must come BEFORE DPI groups (groups reference app IDs)
        await cartography.intel.unifi.dpi_apps.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 11. DPI groups (depend on DPI apps)
        await cartography.intel.unifi.dpi_groups.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 12. Firewall zones — must come BEFORE firewall policies
        await cartography.intel.unifi.firewall_zones.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 13. Firewall policies (depend on firewall zones)
        await cartography.intel.unifi.firewall_policies.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 14. Network configurations (depend on firewall zones for secure group references)
        await cartography.intel.unifi.network_configs.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 15. Outlets/power monitoring (depend on devices)
        await cartography.intel.unifi.outlets.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 16. Speedtests/WAN performance (depend on devices for gateway)
        await cartography.intel.unifi.speedtests.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 17. System information
        await cartography.intel.unifi.system_info.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 18. Vouchers
        await cartography.intel.unifi.vouchers.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # 19. Admins (requires super-admin privileges; returns empty list gracefully if not available)
        await cartography.intel.unifi.admins.sync(
            neo4j_session,
            controller,
            common_job_parameters,
        )

        # Run post-ingestion analysis jobs
        await _run_unifi_analysis(common_job_parameters, neo4j_session)

        # Record successful sync metadata
        merge_module_sync_metadata(
            neo4j_session,
            group_type="UnifiSite",
            group_id=site_id,
            synced_type="UnifiSite",
            update_tag=update_tag,
            stat_handler=stat_handler,
        )

        logger.info("Completed UniFi ingestion for host %s, site %s", host, site)

    finally:
        if controller:
            await close_controller(controller)


async def _run_unifi_analysis(
    common_job_parameters: dict[str, Any],
    neo4j_session: neo4j.Session,
) -> None:
    """
    Run post-ingestion analysis jobs for UniFi.

    :param common_job_parameters: Common job parameters
    :param neo4j_session: Neo4j session
    """
    logger.debug("Running UniFi post-ingestion analysis jobs")

    # Internet exposure analysis
    run_analysis_and_ensure_deps(
        "unifi_internet_exposure.json",
        UNIFI_ANALYSIS_REQUIREMENTS["unifi_internet_exposure.json"],
        set(UNIFI_MODULE_DEPENDENCIES.keys()),
        common_job_parameters,
        neo4j_session,
    )

    # Firmware compliance analysis
    run_analysis_and_ensure_deps(
        "unifi_firmware_compliance.json",
        UNIFI_ANALYSIS_REQUIREMENTS["unifi_firmware_compliance.json"],
        set(UNIFI_MODULE_DEPENDENCIES.keys()),
        common_job_parameters,
        neo4j_session,
    )

    # Guest network isolation analysis
    run_analysis_and_ensure_deps(
        "unifi_guest_isolation.json",
        UNIFI_ANALYSIS_REQUIREMENTS["unifi_guest_isolation.json"],
        set(UNIFI_MODULE_DEPENDENCIES.keys()),
        common_job_parameters,
        neo4j_session,
    )

    # Device health analysis
    run_analysis_and_ensure_deps(
        "unifi_device_health.json",
        UNIFI_ANALYSIS_REQUIREMENTS["unifi_device_health.json"],
        set(UNIFI_MODULE_DEPENDENCIES.keys()),
        common_job_parameters,
        neo4j_session,
    )

    # Network config audit analysis
    run_analysis_and_ensure_deps(
        "unifi_network_config_audit.json",
        UNIFI_ANALYSIS_REQUIREMENTS["unifi_network_config_audit.json"],
        set(UNIFI_MODULE_DEPENDENCIES.keys()),
        common_job_parameters,
        neo4j_session,
    )

    # Power monitoring analysis
    run_analysis_and_ensure_deps(
        "unifi_power_monitoring.json",
        UNIFI_ANALYSIS_REQUIREMENTS["unifi_power_monitoring.json"],
        set(UNIFI_MODULE_DEPENDENCIES.keys()),
        common_job_parameters,
        neo4j_session,
    )

    # WAN performance analysis
    run_analysis_and_ensure_deps(
        "unifi_wan_performance.json",
        UNIFI_ANALYSIS_REQUIREMENTS["unifi_wan_performance.json"],
        set(UNIFI_MODULE_DEPENDENCIES.keys()),
        common_job_parameters,
        neo4j_session,
    )


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

    # Default values for optional config parameters
    unifi_port = config.unifi_port or 443
    update_tag = config.update_tag or int(__import__("time").time())

    # Determine sites to sync
    sites_to_sync = config.unifi_sites or [config.unifi_site or "default"]

    for site in sites_to_sync:
        logger.info("Syncing UniFi site: %s", site)
        asyncio.run(
            _sync_unifi(
                neo4j_session=neo4j_session,
                host=config.unifi_host,
                username=config.unifi_user,
                password=config.unifi_password,
                site=site,
                port=unifi_port,
                verify_ssl=config.unifi_verify_ssl,
                update_tag=update_tag,
            )
        )
