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

# ============================================================================
# ProxmoxReplicationJob Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxReplicationJobNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxReplicationJob node.

    Represents VM/container replication jobs for disaster recovery.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    job_id: PropertyRef = PropertyRef("job_id", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    guest: PropertyRef = PropertyRef("guest")  # VM ID being replicated
    target: PropertyRef = PropertyRef("target")  # Target node
    type: PropertyRef = PropertyRef("type")  # local or remote
    schedule: PropertyRef = PropertyRef("schedule")  # Replication schedule
    rate: PropertyRef = PropertyRef("rate")  # Rate limit in MB/s
    disable: PropertyRef = PropertyRef("disable")  # Whether job is disabled
    comment: PropertyRef = PropertyRef("comment")
    source: PropertyRef = PropertyRef("source")  # Source node (optional)


@dataclass(frozen=True)
class ProxmoxReplicationJobToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxReplicationJob to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxReplicationJobToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxReplicationJob)-[:RESOURCE]->(:ProxmoxCluster)

    Replication jobs belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxReplicationJobToClusterRelProperties = ProxmoxReplicationJobToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxReplicationJobToVMRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxReplicationJob to ProxmoxVM.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxReplicationJobToVMRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxReplicationJob)-[:REPLICATES]->(:ProxmoxVM)

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
    properties: ProxmoxReplicationJobToVMRelProperties = ProxmoxReplicationJobToVMRelProperties()


@dataclass(frozen=True)
class ProxmoxReplicationJobSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxReplicationJob.

    VM/container replication jobs for disaster recovery.
    """

    label: str = "ProxmoxReplicationJob"
    properties: ProxmoxReplicationJobNodeProperties = ProxmoxReplicationJobNodeProperties()
    sub_resource_relationship: ProxmoxReplicationJobToClusterRel = ProxmoxReplicationJobToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxReplicationJobToVMRel(),
        ]
    )
