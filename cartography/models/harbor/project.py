from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.harbor.tenant import HarborResourceToInstanceRel


@dataclass(frozen=True)
class HarborProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="`{instance}/{project name}`. Project names are unique within an instance.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Project name."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="Numeric Harbor project id."
    )
    owner_name: PropertyRef = PropertyRef(
        "owner_name", description="Name of the user that owns the project."
    )
    public: PropertyRef = PropertyRef(
        "public",
        description="True when anonymous users can pull from the project.",
    )
    repo_count: PropertyRef = PropertyRef(
        "repo_count", description="Number of repositories in the project."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When the project was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="When the project was last updated."
    )


@dataclass(frozen=True)
class HarborProjectSchema(CartographyNodeSchema):
    """A Harbor project, the namespace that groups repositories and carries access control."""

    label: str = "HarborProject"
    properties: HarborProjectNodeProperties = HarborProjectNodeProperties()
    sub_resource_relationship: HarborResourceToInstanceRel = (
        HarborResourceToInstanceRel()
    )
