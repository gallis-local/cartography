from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# ContainerRegistry fields:
# _ont_name - The name of the container registry/repository (REQUIRED)
# _ont_uri - The registry URI/endpoint for pulling images
# _ont_location - The region/location where the registry is hosted
# _ont_created_at - Timestamp when the registry was created
# _ont_size_bytes - Storage size in bytes

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSECRRepository",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="uri", node_field="uri"),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                # _ont_size_bytes: Not directly available in AWSECRRepository model
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPArtifactRegistryRepository",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="uri", node_field="registry_uri"),
                OntologyFieldMapping(ontology_field="location", node_field="location"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="create_time"
                ),
                OntologyFieldMapping(
                    ontology_field="size_bytes", node_field="size_bytes"
                ),
            ],
        ),
    ],
)

gitlab_mapping = OntologyMapping(
    module_name="gitlab",
    nodes=[
        OntologyNodeMapping(
            node_label="GitLabContainerRepository",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="uri", node_field="path"),
                # _ont_location: Not applicable for GitLab (self-hosted or SaaS)
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                OntologyFieldMapping(ontology_field="size_bytes", node_field="size"),
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayContainerRegistryNamespace",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="uri", node_field="endpoint"),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                OntologyFieldMapping(ontology_field="size_bytes", node_field="size"),
            ],
        ),
    ],
)

harbor_mapping = OntologyMapping(
    module_name="harbor",
    nodes=[
        OntologyNodeMapping(
            node_label="HarborRepository",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="uri", node_field="uri"),
                # _ont_location: Not applicable, a Harbor instance is not tied to a region
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="creation_time"
                ),
                # _ont_size_bytes: Not available on the repository, only per artifact
            ],
        ),
    ],
)

CONTAINERREGISTRIES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "harbor": harbor_mapping,
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "gitlab": gitlab_mapping,
    "scaleway": scaleway_mapping,
    "snowflake": OntologyMapping(
        module_name="snowflake",
        nodes=[
            OntologyNodeMapping(
                node_label="SnowflakeImageRepository",
                fields=[
                    OntologyFieldMapping(
                        ontology_field="name", node_field="name", required=True
                    ),
                    OntologyFieldMapping(
                        ontology_field="uri", node_field="repository_url"
                    ),
                    OntologyFieldMapping(
                        ontology_field="created_at", node_field="created_on"
                    ),
                ],
            ),
        ],
    ),
}
