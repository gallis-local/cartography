"""
Proxmox replication job sync module.

Syncs VM/container replication jobs for disaster recovery.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.proxmox.replication import ProxmoxReplicationJobSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


@timeit
def get_replication_jobs(proxmox_client: Any) -> List[Dict[str, Any]]:
    """
    Get all replication jobs in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of replication job dicts
    """
    try:
        return proxmox_client.cluster.replication.get()
    except Exception as e:
        logger.debug(f"Could not fetch replication jobs: {e}")
        return []


# ============================================================================
# TRANSFORM functions
# ============================================================================


def transform_replication_job_data(
    jobs: List[Dict[str, Any]],
    cluster_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform replication job data into standard format.

    :param jobs: Raw replication job data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed replication job dicts
    """
    transformed_jobs = []

    for job in jobs:
        # Required fields
        job_id = job["id"]

        # NEW UID PATTERN: Consistent path-like structure
        # OLD: f"{cluster_id}:{job_id}"
        # NEW: f"{cluster_id}/replication/{job_id}"
        replication_job_id = f"{cluster_id}/replication/{job_id}"

        target = job.get("target")
        source = job.get("source")

        transformed_jobs.append(
            {
                "id": replication_job_id,
                "job_id": job_id,
                "cluster_id": cluster_id,
                "guest": job.get("guest"),  # VM ID
                "target": target,  # Target node name
                "target_node_id": f"{cluster_id}/node/{target}" if target else None,
                "type": job.get("type"),  # local or remote
                "schedule": job.get("schedule"),  # e.g., "*/15" for every 15 min
                "rate": job.get("rate"),  # Rate limit in MB/s
                "disable": job.get("disable", 0) == 1,  # Convert to boolean
                "comment": job.get("comment"),
                "source": source,  # Source node name (optional)
                "source_node_id": f"{cluster_id}/node/{source}" if source else None,
            }
        )

    return transformed_jobs


# ============================================================================
# LOAD functions
# ============================================================================


def load_replication_jobs(
    neo4j_session: neo4j.Session,
    jobs: List[Dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load replication job data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param jobs: List of transformed replication job dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxReplicationJobSchema(),
        jobs,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


# ============================================================================
# SYNC function
# ============================================================================


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync VM/container replication jobs.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Proxmox cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters for GraphJob
    """
    logger.info("Syncing Proxmox replication jobs")

    # GET - retrieve data from API
    raw_jobs = get_replication_jobs(proxmox_client)

    # TRANSFORM - convert to standard format
    transformed_jobs = transform_replication_job_data(raw_jobs, cluster_id)

    # LOAD - ingest to Neo4j
    load_replication_jobs(neo4j_session, transformed_jobs, cluster_id, update_tag)

    # CLEANUP - remove stale jobs
    cleanup(neo4j_session, common_job_parameters)

    logger.info(f"Synced {len(transformed_jobs)} replication jobs")


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Remove stale replication job data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    """
    GraphJob.from_node_schema(ProxmoxReplicationJobSchema(), common_job_parameters).run(
        neo4j_session
    )
