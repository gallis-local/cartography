from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.harbor.tenant import HarborResourceToInstanceRel


@dataclass(frozen=True)
class HarborPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="`{image id}|{package name}|{version}`. One node per package per image.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Package name from the SBOM."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Package version from the SBOM."
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Package ecosystem taken from the package URL, e.g. `deb`, `apk` or `pypi`.",
    )
    purl: PropertyRef = PropertyRef(
        "purl",
        extra_index=True,
        description="Package URL (purl) identifying the package.",
    )
    normalized_id: PropertyRef = PropertyRef(
        "normalized_id",
        extra_index=True,
        description="Normalized `{type}|{namespace/}{name}|{version}` identifier shared with other scanners for cross-tool matching.",
    )
    spdx_id: PropertyRef = PropertyRef(
        "spdx_id", description="SPDX identifier of the package within the SBOM."
    )
    license: PropertyRef = PropertyRef(
        "license", description="License the SBOM concluded or declared for the package."
    )
    supplier: PropertyRef = PropertyRef(
        "supplier", description="Package supplier recorded in the SBOM."
    )
    image_digest: PropertyRef = PropertyRef(
        "image_digest",
        extra_index=True,
        description="Digest of the image the SBOM was generated for.",
    )


@dataclass(frozen=True)
class HarborPackageToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class HarborPackageToImageRel(CartographyRelSchema):
    """Links a package to the image whose SBOM lists it."""

    target_node_label: str = "HarborImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("image_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: HarborPackageToImageRelProperties = HarborPackageToImageRelProperties()


@dataclass(frozen=True)
class HarborPackageSchema(CartographyNodeSchema):
    """A software package listed in the SBOM Harbor generated for an image."""

    label: str = "HarborPackage"
    properties: HarborPackageNodeProperties = HarborPackageNodeProperties()
    sub_resource_relationship: HarborResourceToInstanceRel = (
        HarborResourceToInstanceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [HarborPackageToImageRel()],
    )
