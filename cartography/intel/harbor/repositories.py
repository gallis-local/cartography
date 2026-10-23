import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.harbor.util import get_paginated
from cartography.models.harbor.repository import HarborRepositorySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    instance_id: str,
    projects: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync the repositories of every project.

    :return: The transformed repositories, so the artifact sync knows what to walk.
    """
    raw: list[dict[str, Any]] = []
    for project in projects:
        logger.debug("Fetching Harbor repositories for project %s", project["name"])
        raw.extend(get(session, base_url, project["name"]))
    transformed = transform(raw, instance_id)
    load_repositories(neo4j_session, transformed, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return transformed


@timeit
def get(
    session: requests.Session, base_url: str, project_name: str
) -> list[dict[str, Any]]:
    return get_paginated(session, base_url, f"/projects/{project_name}/repositories")


def transform(
    repositories: list[dict[str, Any]], instance_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for repository in repositories:
        # Harbor names repositories `{project}/{path}`.
        name = repository["name"]
        project_name, repository_path = name.split("/", 1)
        result.append(
            {
                "id": f"{instance_id}/{name}",
                "name": name,
                "uri": f"{instance_id}/{name}",
                "project_name": project_name,
                "project_node_id": f"{instance_id}/{project_name}",
                "repository_path": repository_path,
                "repository_id": repository["id"],
                "description": repository.get("description"),
                "artifact_count": repository.get("artifact_count"),
                "pull_count": repository.get("pull_count"),
                "creation_time": repository.get("creation_time"),
                "update_time": repository.get("update_time"),
            }
        )
    return result


def load_repositories(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    instance_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HarborRepositorySchema(),
        data,
        lastupdated=update_tag,
        INSTANCE_ID=instance_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(HarborRepositorySchema(), common_job_parameters).run(
        neo4j_session
    )
