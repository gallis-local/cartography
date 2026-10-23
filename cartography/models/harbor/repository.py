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
from cartography.models.ontology.labels import CONTAINER_REGISTRY


@dataclass(frozen=True)
class HarborRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="`{instance}/{project}/{repository}`, which is also the URI images are pulled from.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Repository name including its project, e.g. `team/app`.",
    )
    uri: PropertyRef = PropertyRef(
        "uri",
        extra_index=True,
        description="Registry URI without a tag or digest, e.g. `harbor.example.com/team/app`.",
    )
    project_name: PropertyRef = PropertyRef(
        "project_name", description="Name of the project the repository belongs to."
    )
    repository_id: PropertyRef = PropertyRef(
        "repository_id", description="Numeric Harbor repository id."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Free-text repository description."
    )
    artifact_count: PropertyRef = PropertyRef(
        "artifact_count", description="Number of artifacts stored in the repository."
    )
    pull_count: PropertyRef = PropertyRef(
        "pull_count", description="Number of times the repository has been pulled."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When the repository was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="When the repository was last updated."
    )


@dataclass(frozen=True)
class HarborRepositoryToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class HarborRepositoryToProjectRel(CartographyRelSchema):
    """Places a repository inside its Harbor project."""

    target_node_label: str = "HarborProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_node_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_REPOSITORY"
    properties: HarborRepositoryToProjectRelProperties = (
        HarborRepositoryToProjectRelProperties()
    )


@dataclass(frozen=True)
class HarborRepositorySchema(CartographyNodeSchema):
    """A Harbor repository, the collection of artifacts sharing one name within a project.

    Ontology Mapping: The extra label `ContainerRegistry` enables cross-registry queries.
    """

    label: str = "HarborRepository"
    properties: HarborRepositoryNodeProperties = HarborRepositoryNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CONTAINER_REGISTRY])
    sub_resource_relationship: HarborResourceToInstanceRel = (
        HarborResourceToInstanceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [HarborRepositoryToProjectRel()],
    )
