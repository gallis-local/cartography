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
from cartography.models.ontology.labels import IMAGE_TAG


@dataclass(frozen=True)
class HarborImageTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="`{repository id}:{tag name}`.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Tag name, e.g. `latest`."
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Digest of the artifact the tag currently points at.",
    )
    push_time: PropertyRef = PropertyRef(
        "push_time", description="When the tag was pushed."
    )
    pull_time: PropertyRef = PropertyRef(
        "pull_time", description="When the tag was last pulled."
    )
    immutable: PropertyRef = PropertyRef(
        "immutable",
        description="True when a tag immutability rule prevents the tag from being moved or deleted.",
    )
    signed: PropertyRef = PropertyRef(
        "signed", description="True when the tagged artifact carries a signature."
    )


@dataclass(frozen=True)
class HarborImageTagToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class HarborImageTagToRepositoryRel(CartographyRelSchema):
    """Ontology edge from a container registry to the tags it stores."""

    target_node_label: str = "HarborRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REPO_IMAGE"
    properties: HarborImageTagToRepositoryRelProperties = (
        HarborImageTagToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class HarborImageTagToImageRel(CartographyRelSchema):
    """Ontology edge from a tag to the image it currently points at."""

    target_node_label: str = "HarborImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("image_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: HarborImageTagToRepositoryRelProperties = (
        HarborImageTagToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class HarborImageTagSchema(CartographyNodeSchema):
    """A named tag pointing at an artifact in a Harbor repository.

    Ontology Mapping: The extra label `ImageTag` enables cross-registry tag queries.
    """

    label: str = "HarborImageTag"
    properties: HarborImageTagNodeProperties = HarborImageTagNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IMAGE_TAG])
    sub_resource_relationship: HarborResourceToInstanceRel = (
        HarborResourceToInstanceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            HarborImageTagToRepositoryRel(),
            HarborImageTagToImageRel(),
        ],
    )
