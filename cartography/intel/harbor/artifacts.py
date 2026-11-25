import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.harbor.util import encode_repository_name
from cartography.intel.harbor.util import get_paginated
from cartography.intel.harbor.util import pick_report
from cartography.intel.harbor.util import VULNERABILITY_REPORT_MIME_PREFIX
from cartography.models.harbor.image import HarborImageSchema
from cartography.models.harbor.tag import HarborImageTagSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    instance_id: str,
    repositories: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync the container images and tags of every repository.

    :return: The transformed images, so the vulnerability and SBOM syncs know which
        images have a completed scan or SBOM to fetch.
    """
    images: list[dict[str, Any]] = []
    tags: list[dict[str, Any]] = []
    for repository in repositories:
        logger.debug("Fetching Harbor artifacts for repository %s", repository["name"])
        artifacts = get(session, base_url, repository)
        repo_images, repo_tags = transform(artifacts, repository)
        images.extend(repo_images)
        tags.extend(repo_tags)
    load_images(neo4j_session, images, instance_id, update_tag)
    load_tags(neo4j_session, tags, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return images


@timeit
def get(
    session: requests.Session, base_url: str, repository: dict[str, Any]
) -> list[dict[str, Any]]:
    path = (
        f"/projects/{repository['project_name']}/repositories/"
        f"{encode_repository_name(repository['repository_path'])}/artifacts"
    )
    return get_paginated(
        session,
        base_url,
        path,
        {
            "with_tag": "true",
            "with_scan_overview": "true",
            # Ignored by Harbor releases that predate SBOM support.
            "with_sbom_overview": "true",
        },
    )


def transform(
    artifacts: list[dict[str, Any]], repository: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    images: list[dict[str, Any]] = []
    tags: list[dict[str, Any]] = []
    for artifact in artifacts:
        # Charts, WASM modules, and other non-image artifacts are out of scope.
        if artifact["type"] != "IMAGE":
            continue
        digest = artifact["digest"]
        image_id = f"{repository['id']}@{digest}"
        references = artifact.get("references") or []
        extra_attrs = artifact.get("extra_attrs") or {}
        scan = pick_report(
            artifact.get("scan_overview") or {}, VULNERABILITY_REPORT_MIME_PREFIX
        )
        scan_summary = (scan or {}).get("summary") or {}
        scanner = (scan or {}).get("scanner") or {}
        sbom = artifact.get("sbom_overview") or {}
        images.append(
            {
                "id": image_id,
                "digest": digest,
                "uri": repository["uri"],
                "repository_id": repository["id"],
                "project_name": repository["project_name"],
                "repository_path": repository["repository_path"],
                "type": "manifest_list" if references else "image",
                "artifact_type": artifact["type"],
                "media_type": artifact.get("media_type"),
                "manifest_media_type": artifact.get("manifest_media_type"),
                "size": artifact.get("size"),
                "push_time": artifact.get("push_time"),
                "pull_time": artifact.get("pull_time"),
                "architecture": extra_attrs.get("architecture"),
                "os": extra_attrs.get("os"),
                "variant": extra_attrs.get("variant"),
                "created": extra_attrs.get("created"),
                "author": extra_attrs.get("author"),
                "child_image_ids": [
                    f"{repository['id']}@{reference['child_digest']}"
                    for reference in references
                ],
                "scan_status": (scan or {}).get("scan_status"),
                "scan_severity": (scan or {}).get("severity"),
                "scan_total": scan_summary.get("total"),
                "scan_fixable": scan_summary.get("fixable"),
                "scan_end_time": (scan or {}).get("end_time"),
                "scanner_name": scanner.get("name"),
                "scanner_version": scanner.get("version"),
                "sbom_status": sbom.get("scan_status"),
                "sbom_digest": sbom.get("sbom_digest"),
                "sbom_end_time": sbom.get("end_time"),
            }
        )
        for tag in artifact.get("tags") or []:
            tags.append(
                {
                    "id": f"{repository['id']}:{tag['name']}",
                    "name": tag["name"],
                    "digest": digest,
                    "repository_id": repository["id"],
                    "image_id": image_id,
                    "push_time": tag.get("push_time"),
                    "pull_time": tag.get("pull_time"),
                    "immutable": tag.get("immutable"),
                    "signed": tag.get("signed"),
                }
            )
    return images, tags


def load_images(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    instance_id: str,
    update_tag: int,
) -> None:
    # Rows load in order and a manifest list's CONTAINS_IMAGE edges only resolve
    # to children that already exist, so single-platform images go first.
    ordered = sorted(data, key=lambda image: image["type"] == "manifest_list")
    load(
        neo4j_session,
        HarborImageSchema(),
        ordered,
        lastupdated=update_tag,
        INSTANCE_ID=instance_id,
    )


def load_tags(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    instance_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HarborImageTagSchema(),
        data,
        lastupdated=update_tag,
        INSTANCE_ID=instance_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(HarborImageTagSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(HarborImageSchema(), common_job_parameters).run(
        neo4j_session
    )
