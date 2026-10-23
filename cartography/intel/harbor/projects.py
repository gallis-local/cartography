import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.harbor.util import get_paginated
from cartography.models.harbor.project import HarborProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    instance_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync the Harbor projects the credential can see.

    :return: The transformed projects, so the repository sync knows what to walk.
    """
    projects = get(session, base_url)
    transformed = transform(projects, instance_id)
    load_projects(neo4j_session, transformed, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return transformed


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_paginated(session, base_url, "/projects")


def transform(projects: list[dict[str, Any]], instance_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{instance_id}/{project['name']}",
            "name": project["name"],
            "project_id": project["project_id"],
            "owner_name": project.get("owner_name"),
            "public": (project.get("metadata") or {}).get("public") == "true",
            "repo_count": project.get("repo_count"),
            "creation_time": project.get("creation_time"),
            "update_time": project.get("update_time"),
        }
        for project in projects
    ]


def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    instance_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HarborProjectSchema(),
        data,
        lastupdated=update_tag,
        INSTANCE_ID=instance_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(HarborProjectSchema(), common_job_parameters).run(
        neo4j_session
    )
