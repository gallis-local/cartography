"""
Data models for Proxmox backup jobs.

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher

# ProxmoxBackupJob Node Schema


@dataclass(frozen=True)
class ProxmoxBackupJobNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxBackupJob node.

    Represents scheduled backup configurations in Proxmox.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Cluster-scoped identifier for this backup job, in the form `{cluster_id}/backup/{job_id}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    job_id: PropertyRef = PropertyRef(
        "job_id",
        extra_index=True,
        description="Proxmox identifier of the vzdump job under /cluster/backup.",
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id",
        description="Id of the `ProxmoxCluster` this object belongs to. The sync scopes ingestion, analysis and cleanup to a single cluster, so every cross-object join is qualified by this value.",
    )
    schedule: PropertyRef = PropertyRef(
        "schedule",
        description="systemd calendar event that decides when the job runs, e.g. `sat 02:00`.",
    )
    storage: PropertyRef = PropertyRef(
        "storage", description="Name of the storage the backup archives are written to."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="True when the schedule is active. A disabled job stays configured but never runs.",
    )
    mode: PropertyRef = PropertyRef(
        "mode",
        description="How guests are quiesced while being dumped: `snapshot` (no downtime), `suspend` or `stop`.",
    )
    compression: PropertyRef = PropertyRef(
        "compression",
        description="Compression applied to the archive: `zstd`, `lzo`, `gzip`, or `0` when the dump is written uncompressed.",
    )
    mailnotification: PropertyRef = PropertyRef(
        "mailnotification",
        description="When Proxmox mails the job report: `always` or `failure`.",
    )
    mailto: PropertyRef = PropertyRef(
        "mailto",
        description="Comma-separated recipients of the backup job report mail.",
    )
    notes: PropertyRef = PropertyRef(
        "notes",
        description="Note template Proxmox stores alongside each backup this job creates.",
    )
    # Flattened retention (prune-backups) settings. Each is optional and may be None.
    prune_keep_last: PropertyRef = PropertyRef(
        "prune_keep_last",
        description="Number of most-recent backups to retain regardless of age. Null when this retention tier is not configured.",
    )
    prune_keep_hourly: PropertyRef = PropertyRef(
        "prune_keep_hourly",
        description="Number of hourly buckets to keep one backup from. Null when this retention tier is not configured.",
    )
    prune_keep_daily: PropertyRef = PropertyRef(
        "prune_keep_daily",
        description="Number of daily buckets to keep one backup from. Null when this retention tier is not configured.",
    )
    prune_keep_weekly: PropertyRef = PropertyRef(
        "prune_keep_weekly",
        description="Number of weekly buckets to keep one backup from. Null when this retention tier is not configured.",
    )
    prune_keep_monthly: PropertyRef = PropertyRef(
        "prune_keep_monthly",
        description="Number of monthly buckets to keep one backup from. Null when this retention tier is not configured.",
    )
    prune_keep_yearly: PropertyRef = PropertyRef(
        "prune_keep_yearly",
        description="Number of yearly buckets to keep one backup from. Null when this retention tier is not configured.",
    )
    repeat_missed: PropertyRef = PropertyRef(
        "repeat_missed",
        description="True when a run missed while the node was down is executed as soon as possible instead of skipped.",
    )


@dataclass(frozen=True)
class ProxmoxBackupJobToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxBackupJobToClusterRel(CartographyRelSchema):
    """
    Backup jobs belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxBackupJobToClusterRelProperties = (
        ProxmoxBackupJobToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxBackupJobToStorageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxBackupJobToStorageRel(CartographyRelSchema):
    """
    Backup jobs target storage backends.
    """

    target_node_label: str = "ProxmoxStorage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "storage_id"
            ),  # Full storage ID (cluster_id/storage/name)
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKS_UP_TO"
    properties: ProxmoxBackupJobToStorageRelProperties = (
        ProxmoxBackupJobToStorageRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxBackupJobSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxBackupJob.

    Backup jobs define scheduled VM/container backup configurations.
    """

    label: str = "ProxmoxBackupJob"
    properties: ProxmoxBackupJobNodeProperties = ProxmoxBackupJobNodeProperties()
    sub_resource_relationship: ProxmoxBackupJobToClusterRel = (
        ProxmoxBackupJobToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxBackupJobToStorageRel(),
        ]
    )


# MatchLink Schema for Backup Job to VM Relationships


@dataclass(frozen=True)
class ProxmoxBackupJobToVMMatchLinkProperties(CartographyRelProperties):
    """
    Properties for backup job to VM BACKS_UP relationship.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxBackupJobToVMMatchLink(CartographyRelSchema):
    """
    Connects backup jobs to the VMs they back up.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid"),  # Integer VMID
            "cluster_id": PropertyRef("cluster_id"),  # Scope to same cluster
        }
    )
    source_node_label: str = "ProxmoxBackupJob"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("backup_job_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKS_UP"
    properties: ProxmoxBackupJobToVMMatchLinkProperties = (
        ProxmoxBackupJobToVMMatchLinkProperties()
    )
