import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fleetdm.utils import paginated_get
from cartography.models.fleetdm.host import FleetDMHostSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_HOSTS_URL = "/api/v1/fleet/hosts"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting FleetDM hosts sync")
    hosts = get(api_session, base_url)
    transformed = transform(hosts)
    load_hosts(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed FleetDM hosts sync")


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}{_HOSTS_URL}"
    params = {
        "populate_software": "without_vulnerability_details",
        "populate_policies": "true",
        "populate_users": "true",
        "populate_labels": "true",
    }
    return list(paginated_get(api_session, url, params=params))


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for host in api_result:
        issues = host.get("issues") or {}
        result.append(
            {
                "id": str(host.get("id")),
                "hostname": host.get("hostname"),
                "display_name": host.get("display_name"),
                "uuid": host.get("uuid"),
                "platform": host.get("platform"),
                "os_version": host.get("os_version"),
                "osquery_version": host.get("osquery_version"),
                "build": host.get("build"),
                "platform_like": host.get("platform_like"),
                "code_name": host.get("code_name"),
                "cpu_type": host.get("cpu_type"),
                "cpu_subtype": host.get("cpu_subtype"),
                "cpu_brand": host.get("cpu_brand"),
                "cpu_physical_cores": host.get("cpu_physical_cores"),
                "cpu_logical_cores": host.get("cpu_logical_cores"),
                "hardware_vendor": host.get("hardware_vendor"),
                "hardware_model": host.get("hardware_model"),
                "hardware_version": host.get("hardware_version"),
                "hardware_serial": host.get("hardware_serial"),
                "computer_name": host.get("computer_name"),
                "memory": host.get("memory"),
                "uptime": host.get("uptime"),
                "public_ip": host.get("public_ip"),
                "primary_ip": host.get("primary_ip"),
                "primary_mac": host.get("primary_mac"),
                "status": host.get("status"),
                "seen_time": host.get("seen_time"),
                "last_enrolled_at": host.get("last_enrolled_at"),
                "distributed_interval": host.get("distributed_interval"),
                "config_tls_refresh": host.get("config_tls_refresh"),
                "logger_tls_period": host.get("logger_tls_period"),
                "gigs_disk_space_available": host.get("gigs_disk_space_available"),
                "percent_disk_space_available": host.get(
                    "percent_disk_space_available",
                ),
                "gigs_total_disk_space": host.get("gigs_total_disk_space"),
                "team_name": host.get("team_name"),
                "fleet_name": host.get("fleet_name"),
                "fleet_id": str(host["fleet_id"]) if host.get("fleet_id") else None,
                "failing_policies_count": issues.get("failing_policies_count"),
                "critical_vulnerabilities_count": issues.get(
                    "critical_vulnerabilities_count",
                ),
                "created_at": host.get("created_at"),
                "updated_at": host.get("updated_at"),
                "last_restarted_at": host.get("last_restarted_at"),
            }
        )
    return result


@timeit
def load_hosts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMHostSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FleetDMHostSchema(), common_job_parameters).run(
        neo4j_session,
    )
