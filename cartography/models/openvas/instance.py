"""
Data model for the OpenVASInstance node.

The tenant-like root node that scopes every OpenVAS resource in the graph.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class OpenVASInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for this GVM deployment: host:port, the socket path, or the configured override.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="Display name of this GVM deployment."
    )
    host: PropertyRef = PropertyRef(
        "host", description="Hostname or IP of the gvmd GMP endpoint."
    )
    port: PropertyRef = PropertyRef(
        "port", description="TCP port of the gvmd GMP endpoint."
    )
    user: PropertyRef = PropertyRef(
        "user", description="GVM user cartography authenticated to GMP as."
    )


@dataclass(frozen=True)
class OpenVASInstanceSchema(CartographyNodeSchema):
    """
    Represents a single GVM (Greenbone Vulnerability Management) instance.

    This is the root node of the module. All OpenVAS resources point RESOURCE
    edges at it and cleanup is scoped through it, so this node must never be
    scoped itself.
    """

    label: str = "OpenVASInstance"
    properties: OpenVASInstanceNodeProperties = OpenVASInstanceNodeProperties()
    scoped_cleanup: bool = False
