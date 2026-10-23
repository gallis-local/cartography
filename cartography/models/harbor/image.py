from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.harbor.tenant import HarborResourceToInstanceRel
from cartography.models.ontology.labels import IMAGE
from cartography.models.ontology.labels import IMAGE_MANIFEST_LIST


@dataclass(frozen=True)
class HarborImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="`{repository id}@{digest}`. The same digest pushed to two repositories is two nodes.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Content-addressable digest of the artifact manifest.",
    )
    uri: PropertyRef = PropertyRef(
        "uri",
        extra_index=True,
        description="Repository URI without a tag or digest.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="`image` for a single-platform image or `manifest_list` for a multi-architecture index.",
    )
    artifact_type: PropertyRef = PropertyRef(
        "artifact_type",
        description="Artifact type Harbor reports, e.g. `IMAGE`.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type", description="Media type of the artifact config."
    )
    manifest_media_type: PropertyRef = PropertyRef(
        "manifest_media_type", description="Media type of the artifact manifest."
    )
    size: PropertyRef = PropertyRef("size", description="Artifact size in bytes.")
    push_time: PropertyRef = PropertyRef(
        "push_time", description="When the artifact was pushed."
    )
    pull_time: PropertyRef = PropertyRef(
        "pull_time", description="When the artifact was last pulled."
    )
    architecture: PropertyRef = PropertyRef(
        "architecture", description="CPU architecture from the image config."
    )
    os: PropertyRef = PropertyRef(
        "os", description="Operating system from the image config."
    )
    variant: PropertyRef = PropertyRef(
        "variant", description="CPU architecture variant from the image config."
    )
    created: PropertyRef = PropertyRef(
        "created", description="Build timestamp from the image config."
    )
    author: PropertyRef = PropertyRef(
        "author", description="Author recorded in the image config."
    )
    child_image_ids: PropertyRef = PropertyRef(
        "child_image_ids",
        description="Ids of the platform-specific images a manifest list points at.",
    )
    scan_status: PropertyRef = PropertyRef(
        "scan_status",
        extra_index=True,
        description="Vulnerability scan state: `Success`, `Running`, `Error`, `Stopped`, or null when never scanned.",
    )
    scan_severity: PropertyRef = PropertyRef(
        "scan_severity",
        description="Highest severity found by the last vulnerability scan.",
    )
    scan_total: PropertyRef = PropertyRef(
        "scan_total", description="Number of vulnerabilities in the last scan."
    )
    scan_fixable: PropertyRef = PropertyRef(
        "scan_fixable",
        description="Number of vulnerabilities in the last scan that have a fixed version.",
    )
    scan_end_time: PropertyRef = PropertyRef(
        "scan_end_time", description="When the last vulnerability scan finished."
    )
    scanner_name: PropertyRef = PropertyRef(
        "scanner_name", description="Scanner that produced the last vulnerability scan."
    )
    scanner_version: PropertyRef = PropertyRef(
        "scanner_version", description="Version of the scanner."
    )
    sbom_status: PropertyRef = PropertyRef(
        "sbom_status",
        extra_index=True,
        description="SBOM generation state: `Success`, `Running`, `Error`, `Stopped`, or null when no SBOM was generated.",
    )
    sbom_digest: PropertyRef = PropertyRef(
        "sbom_digest", description="Digest of the stored SBOM artifact."
    )
    sbom_end_time: PropertyRef = PropertyRef(
        "sbom_end_time", description="When SBOM generation finished."
    )


@dataclass(frozen=True)
class HarborImageToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class HarborImageToRepositoryRel(CartographyRelSchema):
    """Stores an image in a repository."""

    target_node_label: str = "HarborRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IMAGE"
    properties: HarborImageToRepositoryRelProperties = (
        HarborImageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class HarborImageContainsImageRel(CartographyRelSchema):
    """Points a manifest list at its platform-specific child images."""

    target_node_label: str = "HarborImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("child_image_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: HarborImageToRepositoryRelProperties = (
        HarborImageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class HarborImageSchema(CartographyNodeSchema):
    """A digest-addressed artifact in a Harbor repository: a container image or a multi-architecture manifest list.

    Ontology Mapping: single-platform images carry the `Image` label and manifest
    lists carry `ImageManifestList`, so they join the cross-registry image queries.
    """

    label: str = "HarborImage"
    properties: HarborImageNodeProperties = HarborImageNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            IMAGE.when(type="image"),
            IMAGE_MANIFEST_LIST.when(type="manifest_list"),
        ],
    )
    sub_resource_relationship: HarborResourceToInstanceRel = (
        HarborResourceToInstanceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            HarborImageToRepositoryRel(),
            HarborImageContainsImageRel(),
        ],
    )
