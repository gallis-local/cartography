"""
Sync Proxmox backup jobs.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.models.proxmox.backup import ProxmoxBackupJobSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


@timeit
def get_backup_jobs(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all backup jobs in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of backup job dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.backup.get()


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# ============================================================================


def transform_backup_job_data(
    jobs: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform backup job data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param jobs: Raw backup job data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed backup job dicts
    """
    transformed_jobs = []

    for job in jobs:
        # Required field - use direct access
        job_id = job["id"]

        # Parse prune settings if they exist. The Proxmox API returns a map like:
        # {"keep-last": "2", "keep-weekly": "4", ...}
        # Neo4j properties cannot store maps, so we flatten into individual primitive properties.
        prune_cfg = job.get("prune-backups") or {}

        def _convert(value: Any) -> Any:
            # Convert numeric strings to int; leave others (None or non-digit strings) as-is
            if isinstance(value, str) and value.isdigit():
                try:
                    return int(value)
                except ValueError:
                    return value
            return value

        prune_keep_last = _convert(prune_cfg.get("keep-last"))
        prune_keep_hourly = _convert(prune_cfg.get("keep-hourly"))
        prune_keep_daily = _convert(prune_cfg.get("keep-daily"))
        prune_keep_weekly = _convert(prune_cfg.get("keep-weekly"))
        prune_keep_monthly = _convert(prune_cfg.get("keep-monthly"))
        prune_keep_yearly = _convert(prune_cfg.get("keep-yearly"))

        # NEW UID PATTERN: Consistent path-like structure
        # OLD: f"{cluster_id}:{job_id}"
        # NEW: f"{cluster_id}/backup/{job_id}"
        transformed_jobs.append(
            {
                "id": f"{cluster_id}/backup/{job_id}",
                "job_id": job_id,
                "cluster_id": cluster_id,
                "schedule": job.get("schedule"),
                "storage": job.get("storage"),
                "storage_id": f"{cluster_id}/storage/{job['storage']}" if job.get("storage") else None,
                "enabled": job.get("enabled", True),
                "mode": job.get("mode", "snapshot"),
                "compression": job.get("compress"),
                "mailnotification": job.get("mailnotification"),
                "mailto": job.get("mailto"),
                "notes": job.get("notes"),
                "prune_keep_last": prune_keep_last,
                "prune_keep_hourly": prune_keep_hourly,
                "prune_keep_daily": prune_keep_daily,
                "prune_keep_weekly": prune_keep_weekly,
                "prune_keep_monthly": prune_keep_monthly,
                "prune_keep_yearly": prune_keep_yearly,
                "repeat_missed": job.get("repeat-missed", False),
            }
        )

    return transformed_jobs


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# ============================================================================


def load_backup_jobs(
    neo4j_session: neo4j.Session,
    jobs: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load backup job data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param jobs: List of transformed backup job dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxBackupJobSchema(),
        jobs,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_backup_job_vm_relationships(
    neo4j_session: neo4j.Session,
    job_vms: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Create relationships between backup jobs and the VMs they back up.

    Uses MatchLinks to connect backup jobs to VMs.

    :param neo4j_session: Neo4j session
    :param job_vms: List of job-VM mappings
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    from cartography.client.core.tx import load_matchlinks
    from cartography.models.proxmox.backup import ProxmoxBackupJobToVMMatchLink

    if not job_vms:
        return

    load_matchlinks(
        neo4j_session,
        ProxmoxBackupJobToVMMatchLink(),
        job_vms,
        lastupdated=update_tag,
        _sub_resource_label="ProxmoxCluster",
        _sub_resource_id=cluster_id,
    )


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# ============================================================================


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync backup job data.

    Follows Cartography's Get → Transform → Load pattern.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox backup jobs")

    # GET - retrieve data from API
    jobs = get_backup_jobs(proxmox_client)

    if not jobs:
        logger.info("No backup jobs found")
        return

    # Collect job-VM relationships
    job_vms = []
    for job in jobs:
        job_id = job["id"]

        # Parse vmid field which can be:
        # - Single VMID: "100"
        # - Multiple VMIDs: "100,101,102"
        # - All VMs: "all"
        # - Pool: "pool:poolname"
        if "vmid" in job and job["vmid"] != "all":
            vmid_str = job["vmid"]

            # Skip pool references for now (would need pool member lookup)
            if not vmid_str.startswith("pool:"):
                vmids = [
                    int(vid.strip())
                    for vid in vmid_str.split(",")
                    if vid.strip().isdigit()
                ]
                for vmid in vmids:
                    job_vms.append(
                        {
                            "job_id": job_id,
                            "vmid": vmid,
                            "cluster_id": cluster_id,
                        }
                    )

    # TRANSFORM - manipulate data for ingestion
    transformed_jobs = transform_backup_job_data(jobs, cluster_id)

    # LOAD - ingest to Neo4j
    load_backup_jobs(neo4j_session, transformed_jobs, cluster_id, update_tag)
    load_backup_job_vm_relationships(neo4j_session, job_vms, cluster_id, update_tag)

    logger.info(
        f"Synced {len(transformed_jobs)} backup jobs covering {len(job_vms)} VMs"
    )
