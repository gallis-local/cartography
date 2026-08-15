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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    comment: PropertyRef = PropertyRef("comment")
    credential_type: PropertyRef = PropertyRef("credential_type")
    allow_insecure: PropertyRef = PropertyRef("allow_insecure")
    creation_time: PropertyRef = PropertyRef("creation_time")
    modification_time: PropertyRef = PropertyRef("modification_time")


@dataclass(frozen=True)
class OpenVASCredentialToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASCredential)
@dataclass(frozen=True)
class OpenVASCredentialToInstanceRel(CartographyRelSchema):
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
    label: str = "OpenVASCredential"
    properties: OpenVASCredentialNodeProperties = OpenVASCredentialNodeProperties()
    sub_resource_relationship: OpenVASCredentialToInstanceRel = (
        OpenVASCredentialToInstanceRel()
    )


@dataclass(frozen=True)
class OpenVASPortListNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instance_id: PropertyRef = PropertyRef("OPENVAS_INSTANCE_ID", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    comment: PropertyRef = PropertyRef("comment")
    port_count: PropertyRef = PropertyRef("port_count")
    creation_time: PropertyRef = PropertyRef("creation_time")
    modification_time: PropertyRef = PropertyRef("modification_time")


@dataclass(frozen=True)
class OpenVASPortListToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:OpenVASInstance)-[:RESOURCE]->(:OpenVASPortList)
@dataclass(frozen=True)
class OpenVASPortListToInstanceRel(CartographyRelSchema):
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
    label: str = "OpenVASPortList"
    properties: OpenVASPortListNodeProperties = OpenVASPortListNodeProperties()
    sub_resource_relationship: OpenVASPortListToInstanceRel = (
        OpenVASPortListToInstanceRel()
    )
