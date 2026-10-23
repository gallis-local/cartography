import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.harbor.util import encode_repository_name
from cartography.intel.harbor.util import get_json
from cartography.intel.trivy.util import make_normalized_package_id
from cartography.intel.trivy.util import parse_purl
from cartography.models.harbor.package import HarborPackageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# SPDX marks the package that describes the scanned image itself with this purpose.
_IMAGE_ROOT_PURPOSE = "CONTAINER"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    instance_id: str,
    images: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync the packages listed in the SBOM Harbor generated for each image.

    Only images whose SBOM generation completed are fetched. Manifest lists are
    skipped: their children carry the SBOMs.
    """
    packages: list[dict[str, Any]] = []
    for image in images:
        if image["type"] != "image" or image["sbom_status"] != "Success":
            continue
        logger.debug("Fetching Harbor SBOM for image %s", image["id"])
        sbom = get(session, base_url, image)
        packages.extend(transform(sbom, image))
    load_packages(neo4j_session, packages, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    session: requests.Session, base_url: str, image: dict[str, Any]
) -> dict[str, Any]:
    path = (
        f"/projects/{image['project_name']}/repositories/"
        f"{encode_repository_name(image['repository_path'])}/artifacts/"
        f"{image['digest']}/additions/sbom"
    )
    return get_json(session, base_url, path)


def _find_spdx_document(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Harbor serves the SPDX JSON document the scanner produced. Depending on the
    Harbor release it arrives bare or under a wrapper key (`sbom`, or a report MIME
    type), so look for the document that has a `packages` list.
    """
    if "packages" in payload:
        return payload
    for value in payload.values():
        if isinstance(value, dict):
            if "packages" in value:
                return value
            nested = value.get("sbom")
            if isinstance(nested, dict) and "packages" in nested:
                return nested
    raise ValueError("Harbor SBOM response does not contain an SPDX packages list.")


def transform(payload: dict[str, Any], image: dict[str, Any]) -> list[dict[str, Any]]:
    document = _find_spdx_document(payload)
    packages: dict[str, dict[str, Any]] = {}
    for package in document["packages"] or []:
        if package.get("primaryPackagePurpose") == _IMAGE_ROOT_PURPOSE:
            continue
        name = package["name"]
        version = package.get("versionInfo")
        purl = next(
            (
                ref["referenceLocator"]
                for ref in package.get("externalRefs") or []
                if ref.get("referenceType") == "purl"
            ),
            None,
        )
        parsed_purl = parse_purl(purl)
        package_type = parsed_purl["type"] if parsed_purl else None
        node_id = f"{image['id']}|{name}|{version}"
        packages[node_id] = {
            "id": node_id,
            "name": name,
            "version": version,
            "type": package_type,
            "purl": purl,
            "normalized_id": make_normalized_package_id(
                purl=purl, name=name, version=version, pkg_type=package_type
            ),
            "spdx_id": package.get("SPDXID"),
            "license": _license(package),
            "supplier": package.get("supplier"),
            "image_id": image["id"],
            "image_digest": image["digest"],
        }
    return list(packages.values())


def _license(package: dict[str, Any]) -> str | None:
    # SPDX uses NOASSERTION / NONE for "no statement"; treat those as missing.
    for field in ("licenseConcluded", "licenseDeclared"):
        value = package.get(field)
        if value and value not in ("NOASSERTION", "NONE"):
            return str(value)
    return None


def load_packages(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    instance_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HarborPackageSchema(),
        data,
        lastupdated=update_tag,
        INSTANCE_ID=instance_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(HarborPackageSchema(), common_job_parameters).run(
        neo4j_session
    )
