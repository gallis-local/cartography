"""
Proxmox replication job sync module.

Syncs VM/container replication jobs for disaster recovery.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.proxmox.replication import ProxmoxReplicationJobSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_replication_jobs(proxmox_client: Any) -> list[dict[str, Any]]:
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


def transform_replication_job_data(
    jobs: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
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


def load_replication_jobs(
    neo4j_session: neo4j.Session,
    jobs: list[dict[str, Any]],
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


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
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

    raw_jobs = get_replication_jobs(proxmox_client)

    transformed_jobs = transform_replication_job_data(raw_jobs, cluster_id)

    load_replication_jobs(neo4j_session, transformed_jobs, cluster_id, update_tag)

    logger.info(f"Synced {len(transformed_jobs)} replication jobs")

    cleanup(neo4j_session, common_job_parameters)

def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    """
    Remove stale replication job data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    """
    GraphJob.from_node_schema(ProxmoxReplicationJobSchema(), common_job_parameters).run(
        neo4j_session
    )
