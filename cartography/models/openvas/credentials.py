"""
Data models for OpenVAS credentials and port lists.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OpenVASCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The GVM UUID of this credential.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="The credential's display name."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment set on the credential."
    )
    credential_type: PropertyRef = PropertyRef(
        "credential_type",
        description="Authentication type this credential provides (e.g. usk, up, snmp).",
    )
    allow_insecure: PropertyRef = PropertyRef(
        "allow_insecure",
        description="Whether the credential may be used over an insecure/unencrypted channel.",
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When the credential was created."
    )
    modification_time: PropertyRef = PropertyRef(
        "modification_time", description="When the credential was last modified."
    )


@dataclass(frozen=True)
class OpenVASCredentialToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASCredential)
class OpenVASCredentialToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this credential."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASCredentialToInstanceRelProperties = (
        OpenVASCredentialToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASCredentialSchema(CartographyNodeSchema):
    """A GVM credential used for authenticated (SSH/SMB/ESXi/SNMP) scanning of targets."""

    label: str = "OpenVASCredential"
    properties: OpenVASCredentialNodeProperties = OpenVASCredentialNodeProperties()
    sub_resource_relationship: OpenVASCredentialToInstanceRel = (
        OpenVASCredentialToInstanceRel()
    )


@dataclass(frozen=True)
class OpenVASPortListNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The GVM UUID of this port list.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="The port list's display name.")
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment set on the port list."
    )
    port_count: PropertyRef = PropertyRef(
        "port_count", description="Number of ports/port ranges defined in this list."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="When the port list was created."
    )
    modification_time: PropertyRef = PropertyRef(
        "modification_time", description="When the port list was last modified."
    )


@dataclass(frozen=True)
class OpenVASPortListToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASPortList)
class OpenVASPortListToInstanceRel(CartographyRelSchema):
    """The OpenVASInstance that owns this port list."""

    target_node_label: str = "OpenVASInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenVASPortListToInstanceRelProperties = (
        OpenVASPortListToInstanceRelProperties()
    )


@dataclass(frozen=True)
class OpenVASPortListSchema(CartographyNodeSchema):
    """A GVM port list: the set of ports/port ranges a scan target is scoped to."""

    label: str = "OpenVASPortList"
    properties: OpenVASPortListNodeProperties = OpenVASPortListNodeProperties()
    sub_resource_relationship: OpenVASPortListToInstanceRel = (
        OpenVASPortListToInstanceRel()
    )
