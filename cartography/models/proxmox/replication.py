"""
Data models for Proxmox replication jobs.

Follows Cartography's modern data model pattern.
"""

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

# ProxmoxReplicationJob Node Relationships to Nodes

# ProxmoxReplicationJob Node Schema


@dataclass(frozen=True)
class ProxmoxReplicationJobNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxReplicationJob node.

    Represents VM/container replication jobs for disaster recovery.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this replication job, in the form `{cluster_id}/replication/{job_id}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    job_id: PropertyRef = PropertyRef(
        "job_id",
        extra_index=True,
        description="Proxmox replication job id, in the form `{vmid}-{index}`.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    guest: PropertyRef = PropertyRef(
        "guest",
        description="Numeric id of the guest whose volumes this job replicates.",
    )
    target: PropertyRef = PropertyRef(
        "target", description="Name of the node the guest's volumes are replicated to."
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Replication transport reported by Proxmox, e.g. `local` for ZFS replication between nodes of the same cluster.",
    )
    schedule: PropertyRef = PropertyRef(
        "schedule",
        description="systemd calendar event controlling how often the job runs, e.g. `*/15` for every 15 minutes.",
    )
    rate: PropertyRef = PropertyRef(
        "rate",
        description="Bandwidth cap for the replication stream in MB/s. Null when the stream is unlimited.",
    )
    disable: PropertyRef = PropertyRef(
        "disable", description="True when the job is switched off and will not run."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-text comment stored on the replication job."
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="Name of the node the volumes are replicated from. Null when Proxmox reports no explicit source.",
    )


@dataclass(frozen=True)
class ProxmoxReplicationJobToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxReplicationJobToClusterRel(CartographyRelSchema):
    """
    Replication jobs belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxReplicationJobToClusterRelProperties = (
        ProxmoxReplicationJobToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxReplicationJobToVMRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxReplicationJobToVMRel(CartographyRelSchema):
    """
    Replication jobs replicate specific VMs/containers.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("guest"),
            "cluster_id": PropertyRef("cluster_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPLICATES"
    properties: ProxmoxReplicationJobToVMRelProperties = (
        ProxmoxReplicationJobToVMRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxReplicationJobToTargetNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxReplicationJobToTargetNodeRel(CartographyRelSchema):
    """
    Replication jobs replicate data to a target node (DR destination).
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("target_node_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPLICATES_TO"
    properties: ProxmoxReplicationJobToTargetNodeRelProperties = (
        ProxmoxReplicationJobToTargetNodeRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxReplicationJobToSourceNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxReplicationJobToSourceNodeRel(CartographyRelSchema):
    """
    Replication jobs originate from a source node (optional, for cross-node jobs).
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("source_node_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPLICATES_FROM"
    properties: ProxmoxReplicationJobToSourceNodeRelProperties = (
        ProxmoxReplicationJobToSourceNodeRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxReplicationJobSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxReplicationJob.

    VM/container replication jobs for disaster recovery.
    """

    label: str = "ProxmoxReplicationJob"
    properties: ProxmoxReplicationJobNodeProperties = (
        ProxmoxReplicationJobNodeProperties()
    )
    sub_resource_relationship: ProxmoxReplicationJobToClusterRel = (
        ProxmoxReplicationJobToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxReplicationJobToVMRel(),
            ProxmoxReplicationJobToTargetNodeRel(),
            ProxmoxReplicationJobToSourceNodeRel(),
        ]
    )
