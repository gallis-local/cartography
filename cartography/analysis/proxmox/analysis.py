"""
Typed analysis jobs for Proxmox.

Every job is scoped with ``ScopeById("ProxmoxCluster", "CLUSTER_ID")``, which both
prefixes each statement with ``MATCH (scope:ProxmoxCluster {id: $CLUSTER_ID})
-[:RESOURCE]->(var)`` and scopes the generated cleanup. That matters here because a
single Cartography run can sync several Proxmox clusters: an unscoped cleanup would
either delete another cluster's findings or keep refreshing them so they never
expire.

Only the variable named in ``scope_on`` is constrained by that prefix. Nodes reached
by traversing from it are deliberately left unfiltered: the relationship already
confines them to the same cluster, and re-inlining ``$CLUSTER_ID`` inside a match is
rejected outright (see ``tests/unit/cartography/graph/test_analysis.py``). Where a
statement needs to ask "does this cluster have any X at all", with no scoped variable
to hang off, it walks ``(v)<-[:RESOURCE]-(:ProxmoxCluster)-[:RESOURCE]->(:X)``
instead.

The generated cleanup also REMOVEs every property these jobs set, before the
statements run. That is what keeps a finding from going stale. These statements only
ever set a flag to true, so without the reset a node flagged once would stay flagged
forever -- a VM would keep reporting ``backup_risk`` long after a backup job started
covering it.
"""

from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import SetProperty

PROXMOX_BACKUP_ANALYSIS = AnalysisJob(
    name="Proxmox backup job analysis",
    short_name="proxmox_backup_analysis",
    scope=ScopeById(
        "ProxmoxCluster",
        "CLUSTER_ID",
        scope_on=("b", "b", "v", "b", "b"),
    ),
    statements=(
        AnalysisStatement(
            comment="A disabled backup job protects nothing.",
            match="MATCH (b:ProxmoxBackupJob) WHERE b.enabled = false",
            effects=(SetProperty("b", "backup_risk", True, label="ProxmoxBackupJob"),),
        ),
        AnalysisStatement(
            comment="No prune setting at all means backups accumulate until the "
            "target storage fills up.",
            match="""
            MATCH (b:ProxmoxBackupJob)
            WHERE b.prune_keep_last IS NULL AND b.prune_keep_daily IS NULL
              AND b.prune_keep_weekly IS NULL AND b.prune_keep_monthly IS NULL
              AND b.prune_keep_yearly IS NULL
            """,
            effects=(
                SetProperty("b", "retention_risk", True, label="ProxmoxBackupJob"),
            ),
        ),
        AnalysisStatement(
            comment="Templates are not backed up, so they are excluded.",
            match="""
            MATCH (v:ProxmoxVM)
            WHERE v.template = false
              AND NOT EXISTS {
                MATCH (b:ProxmoxBackupJob)-[:BACKS_UP]->(v)
              }
            """,
            effects=(SetProperty("v", "backup_risk", True, label="ProxmoxVM"),),
        ),
        AnalysisStatement(
            comment="A backup job whose target is nearly full is about to start "
            "failing.",
            match="""
            MATCH (b:ProxmoxBackupJob)-[:BACKS_UP_TO]->(s:ProxmoxStorage)
            WHERE s.total > 0 AND (s.used * 1.0 / s.total) > 0.9
            """,
            effects=(SetProperty("b", "storage_risk", True, label="ProxmoxBackupJob"),),
        ),
        AnalysisStatement(
            comment="A backup job nobody is told about when it fails is a backup "
            "job you cannot rely on.",
            match="""
            MATCH (b:ProxmoxBackupJob)
            WHERE b.mailnotification IS NULL
               OR b.mailnotification = 'never'
               OR (b.mailnotification = 'failure' AND (b.mailto IS NULL OR b.mailto = ''))
            """,
            effects=(
                SetProperty("b", "notification_risk", True, label="ProxmoxBackupJob"),
            ),
        ),
    ),
)

PROXMOX_CERTIFICATE_ANALYSIS = AnalysisJob(
    name="Proxmox certificate analysis",
    short_name="proxmox_certificate_analysis",
    scope=ScopeById(
        "ProxmoxCluster",
        "CLUSTER_ID",
        scope_on=("c", "c", "c", "c", "c", "n"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (c:ProxmoxCertificate) WHERE c.is_expired = true",
            effects=(
                SetProperties(
                    "c",
                    {"cert_risk": True, "cert_status": "expired"},
                    label="ProxmoxCertificate",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (c:ProxmoxCertificate) WHERE c.expires_soon = true",
            effects=(
                SetProperties(
                    "c",
                    {"cert_risk": True, "cert_status": "expiring_soon"},
                    label="ProxmoxCertificate",
                ),
            ),
        ),
        AnalysisStatement(
            comment="Informational only: far enough out that it is not yet a risk, "
            "but worth surfacing. Runs after the two statements above so it cannot "
            "overwrite a more urgent status.",
            match="""
            MATCH (c:ProxmoxCertificate)
            WHERE c.expires_in_days <= 90 AND c.expires_in_days > 30
            """,
            effects=(
                SetProperty(
                    "c",
                    "cert_status",
                    "expiring_within_90d",
                    label="ProxmoxCertificate",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (c:ProxmoxCertificate)
            WHERE c.public_key_type = 'RSA' AND c.public_key_bits < 2048
            """,
            effects=(
                SetProperties(
                    "c",
                    {"cert_risk": True, "cert_weak_key": True},
                    label="ProxmoxCertificate",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (c:ProxmoxCertificate) WHERE c.public_key_type IN ['DSA', 'DSS']",
            effects=(
                SetProperties(
                    "c",
                    {"cert_risk": True, "cert_deprecated_algo": True},
                    label="ProxmoxCertificate",
                ),
            ),
        ),
        AnalysisStatement(
            comment="Every Proxmox node serves its API over TLS, so a node with no "
            "certificate in the graph means we could not read one.",
            match="""
            MATCH (n:ProxmoxNode)
            WHERE NOT EXISTS {
                MATCH (c:ProxmoxCertificate)-[:HAS_CERTIFICATE]->(n)
            }
            """,
            effects=(SetProperty("n", "cert_risk", True, label="ProxmoxNode"),),
        ),
    ),
)

PROXMOX_GUEST_AGENT_ANALYSIS = AnalysisJob(
    name="Proxmox guest agent analysis",
    short_name="proxmox_guest_agent_analysis",
    scope=ScopeById(
        "ProxmoxCluster",
        "CLUSTER_ID",
        scope_on=("v", "v", "v", "v"),
    ),
    statements=(
        AnalysisStatement(
            comment="Without the guest agent there is no in-guest visibility: no "
            "hostname, OS or interface data, and no clean shutdown on host reboot.",
            match="""
            MATCH (v:ProxmoxVM)
            WHERE v.template = false AND v.status = 'running'
              AND (v.agent_enabled IS NULL OR v.agent_enabled = false)
            """,
            effects=(SetProperty("v", "agent_risk", True, label="ProxmoxVM"),),
        ),
        AnalysisStatement(
            comment="Agent configured but returning nothing means it is installed "
            "and not running, which is worse than never having enabled it: the host "
            "believes it can talk to the guest.",
            match="""
            MATCH (v:ProxmoxVM)
            WHERE v.template = false AND v.agent_enabled = true
              AND (v.guest_hostname IS NULL OR v.guest_hostname = '')
            """,
            effects=(SetProperty("v", "agent_risk", True, label="ProxmoxVM"),),
        ),
        AnalysisStatement(
            match="""
            MATCH (v:ProxmoxVM)
            WHERE v.template = false AND v.agent_enabled = true
              AND (v.guest_os_name IS NULL OR v.guest_os_name = '')
            """,
            effects=(SetProperty("v", "os_risk", True, label="ProxmoxVM"),),
        ),
        AnalysisStatement(
            comment="Guest operating systems past end of life stop receiving "
            "security updates.",
            match="""
            MATCH (v:ProxmoxVM)
            WHERE v.guest_os_name IN [
                'windows 7', 'windows 8', 'windows 2008', 'windows 2012',
                'centos 7', 'ubuntu 16.04', 'ubuntu 18.04', 'debian 9', 'debian 10'
            ]
            """,
            effects=(SetProperty("v", "os_risk", True, label="ProxmoxVM"),),
        ),
    ),
)

PROXMOX_HA_ANALYSIS = AnalysisJob(
    name="Proxmox HA analysis",
    short_name="proxmox_ha_analysis",
    scope=ScopeById(
        "ProxmoxCluster",
        "CLUSTER_ID",
        scope_on=("hr", "hg", "hr", "hr", "v", "hg"),
    ),
    statements=(
        AnalysisStatement(
            match="""
            MATCH (hr:ProxmoxHAResource)
            WHERE hr.state <> 'started' AND hr.state <> 'running'
            """,
            effects=(SetProperty("hr", "ha_risk", True, label="ProxmoxHAResource"),),
        ),
        AnalysisStatement(
            comment="A restricted group confines its resources to the group's nodes, "
            "so an empty one can never place anything.",
            match="""
            MATCH (hg:ProxmoxHAGroup)
            WHERE hg.restricted = true
              AND NOT EXISTS { MATCH (hg)<-[:MEMBER_OF_HA_GROUP]-() }
            """,
            effects=(SetProperty("hg", "ha_risk", True, label="ProxmoxHAGroup"),),
        ),
        AnalysisStatement(
            comment="max_relocate = 0 means the resource will never move to a "
            "healthy node.",
            match="MATCH (hr:ProxmoxHAResource) WHERE hr.max_relocate = 0",
            effects=(SetProperty("hr", "ha_risk", True, label="ProxmoxHAResource"),),
        ),
        AnalysisStatement(
            comment="max_restart = 0 means a crashed resource stays down.",
            match="MATCH (hr:ProxmoxHAResource) WHERE hr.max_restart = 0",
            effects=(SetProperty("hr", "ha_risk", True, label="ProxmoxHAResource"),),
        ),
        AnalysisStatement(
            comment="Only meaningful on clusters that actually use HA. Without the "
            "EXISTS guard this fires on every VM of every cluster that does not use "
            "HA, and on standalone nodes where HA is not even possible, which makes "
            "the flag useless.",
            match="""
            MATCH (v:ProxmoxVM)
            WHERE v.template = false
              AND EXISTS {
                MATCH (v)<-[:RESOURCE]-(:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxHAResource)
              }
              AND NOT EXISTS {
                MATCH (hr:ProxmoxHAResource)-[:PROTECTS]->(v)
              }
            """,
            effects=(SetProperty("v", "ha_risk", True, label="ProxmoxVM"),),
        ),
        AnalysisStatement(
            comment="nofailback keeps a resource on its failover node after the "
            "preferred node returns, so it silently stops honouring group priority.",
            match="""
            MATCH (hg:ProxmoxHAGroup)
            WHERE hg.nofailback = true
              AND EXISTS {
                MATCH (hg)<-[:MEMBER_OF_HA_GROUP]-(hr:ProxmoxHAResource)
                WHERE hr.state = 'started'
              }
            """,
            effects=(SetProperty("hg", "ha_risk", True, label="ProxmoxHAGroup"),),
        ),
    ),
)

PROXMOX_REPLICATION_ANALYSIS = AnalysisJob(
    name="Proxmox replication job analysis",
    short_name="proxmox_replication_analysis",
    scope=ScopeById(
        "ProxmoxCluster",
        "CLUSTER_ID",
        scope_on=("r", "r", "v", "r", "r"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (r:ProxmoxReplicationJob) WHERE r.disable = true",
            effects=(
                SetProperty(
                    "r", "replication_risk", True, label="ProxmoxReplicationJob"
                ),
            ),
        ),
        AnalysisStatement(
            comment="A replication job with no resolved target replicates nowhere.",
            match="""
            MATCH (r:ProxmoxReplicationJob)
            WHERE NOT EXISTS { MATCH (r)-[:REPLICATES_TO]->() }
            """,
            effects=(
                SetProperty("r", "target_risk", True, label="ProxmoxReplicationJob"),
            ),
        ),
        AnalysisStatement(
            comment="Only meaningful on clusters that actually replicate. Without "
            "the EXISTS guard this fires on every VM of every cluster that does not, "
            "which makes the flag useless.",
            match="""
            MATCH (v:ProxmoxVM)
            WHERE v.template = false
              AND EXISTS {
                MATCH (v)<-[:RESOURCE]-(:ProxmoxCluster)-[:RESOURCE]->(:ProxmoxReplicationJob)
              }
              AND NOT EXISTS {
                MATCH (r:ProxmoxReplicationJob)-[:REPLICATES]->(v)
              }
            """,
            effects=(SetProperty("v", "replication_risk", True, label="ProxmoxVM"),),
        ),
        AnalysisStatement(
            match="""
            MATCH (r:ProxmoxReplicationJob)-[:REPLICATES_TO]->(n:ProxmoxNode)
            WHERE n.status <> 'online'
            """,
            effects=(
                SetProperty("r", "target_risk", True, label="ProxmoxReplicationJob"),
            ),
        ),
        AnalysisStatement(
            comment="Unrated replication can saturate the cluster network during a "
            "large initial sync.",
            match="MATCH (r:ProxmoxReplicationJob) WHERE r.rate IS NULL OR r.rate = 0",
            effects=(
                SetProperty("r", "network_risk", True, label="ProxmoxReplicationJob"),
            ),
        ),
    ),
)

PROXMOX_SECURITY_ANALYSIS = AnalysisJob(
    name="Proxmox security analysis",
    short_name="proxmox_security",
    scope=ScopeById(
        "ProxmoxCluster",
        "CLUSTER_ID",
        scope_on=("v", "n"),
    ),
    statements=(
        AnalysisStatement(
            comment="vmbr0 is the default Proxmox bridge and carries the host's "
            "uplink, so a running guest attached to it is reachable from wherever "
            "that uplink reaches.",
            match="""
            MATCH (v:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(i:ProxmoxNetworkInterface)
            WHERE i.bridge = 'vmbr0' AND v.status = 'running'
            """,
            effects=(SetProperty("v", "exposed_internet", True, label="ProxmoxVM"),),
        ),
        AnalysisStatement(
            match="MATCH (n:ProxmoxNode) WHERE n.status <> 'online'",
            effects=(SetProperty("n", "availability_risk", True, label="ProxmoxNode"),),
        ),
    ),
)

PROXMOX_STORAGE_ANALYSIS = AnalysisJob(
    name="Proxmox storage analysis",
    short_name="proxmox_storage_analysis",
    scope=ScopeById(
        "ProxmoxCluster",
        "CLUSTER_ID",
        scope_on=("s", "s", "s", "n", "s"),
    ),
    statements=(
        AnalysisStatement(
            match="""
            MATCH (s:ProxmoxStorage)
            WHERE s.total > 0 AND (s.used * 1.0 / s.total) > 0.9
            """,
            effects=(
                SetProperties(
                    "s",
                    {"storage_risk": True, "storage_status": "critical"},
                    label="ProxmoxStorage",
                ),
            ),
        ),
        AnalysisStatement(
            comment="Runs after the critical check and excludes its range so the "
            "more urgent status is not downgraded.",
            match="""
            MATCH (s:ProxmoxStorage)
            WHERE s.total > 0 AND (s.used * 1.0 / s.total) > 0.8
              AND (s.used * 1.0 / s.total) <= 0.9
            """,
            effects=(
                SetProperties(
                    "s",
                    {"storage_risk": True, "storage_status": "warning"},
                    label="ProxmoxStorage",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (s:ProxmoxStorage) WHERE s.enabled = false",
            effects=(
                SetProperties(
                    "s",
                    {"storage_risk": True, "storage_status": "disabled"},
                    label="ProxmoxStorage",
                ),
            ),
        ),
        AnalysisStatement(
            comment="A node with no storage attached cannot host a guest.",
            match="""
            MATCH (n:ProxmoxNode)
            WHERE NOT EXISTS {
                MATCH (s:ProxmoxStorage)-[:AVAILABLE_ON]->(n)
            }
            """,
            effects=(SetProperty("n", "storage_risk", True, label="ProxmoxNode"),),
        ),
        AnalysisStatement(
            comment="Storage marked shared but reachable from one node only defeats "
            "the point: guests on it cannot migrate or fail over.",
            match="""
            MATCH (s:ProxmoxStorage)
            WHERE s.shared = true AND COUNT { MATCH (s)-[:AVAILABLE_ON]->() } = 1
            """,
            effects=(
                SetProperties(
                    "s",
                    {"storage_risk": True, "storage_status": "shared_single_node"},
                    label="ProxmoxStorage",
                ),
            ),
        ),
    ),
)

PROXMOX_ONTOLOGY_LINKING = AnalysisJob(
    name="Proxmox - Ontology relationship linking",
    short_name="proxmox_ontology_linking",
    scope=ScopeById(
        "ProxmoxCluster",
        "CLUSTER_ID",
        scope_on=("key", "cert", "cert"),
    ),
    statements=(
        AnalysisStatement(
            comment="Hang the token off the canonical User so 'every API key this "
            "person owns, on every platform' is one query.",
            match="""
            MATCH (key:ProxmoxAPIToken)-[:OWNED_BY]->(pu:ProxmoxUser)
            MATCH (u:User)-[:HAS_ACCOUNT]->(pu)
            """,
            effects=(
                AddRelationship(
                    "u",
                    "OWNS",
                    "key",
                    source_label="User",
                    target_label="ProxmoxAPIToken",
                    # The cluster scope reaches the token, not the canonical User, so
                    # cleanup has to walk in from the target side.
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            comment="Lets 'which devices have expiring certificates' span providers.",
            match="""
            MATCH (cert:ProxmoxCertificate)<-[:HAS_CERTIFICATE]-(pn:ProxmoxNode)
            MATCH (d:Device)-[:OBSERVED_AS]->(pn)
            """,
            effects=(
                AddRelationship(
                    "cert",
                    "HAS_CERTIFICATE",
                    "d",
                    source_label="ProxmoxCertificate",
                    target_label="Device",
                ),
            ),
        ),
        AnalysisStatement(
            comment="Attributes a node's certificate to the users granted access to "
            "that node, so 'certificates this person is responsible for' works.",
            match="""
            MATCH (cert:ProxmoxCertificate)<-[:HAS_CERTIFICATE]-(pn:ProxmoxNode)
            MATCH (pn)<-[:GRANTS_ACCESS_TO]-(acl:ProxmoxACL)
            MATCH (acl)-[:APPLIES_TO_USER]->(pu:ProxmoxUser)
            MATCH (u:User)-[:HAS_ACCOUNT]->(pu)
            """,
            effects=(
                AddRelationship(
                    "u",
                    "OWNS",
                    "cert",
                    source_label="User",
                    target_label="ProxmoxCertificate",
                    # Scope reaches the certificate, not the canonical User.
                    scoped_to="target",
                ),
            ),
        ),
    ),
)

# Ordering matters: the ontology linking job reads ProxmoxAPIToken and
# ProxmoxCertificate nodes, so it runs last, after the risk jobs have finished
# writing. Within the tuple, each job is independent.
PROXMOX_ANALYSIS_JOBS = (
    PROXMOX_BACKUP_ANALYSIS,
    PROXMOX_REPLICATION_ANALYSIS,
    PROXMOX_HA_ANALYSIS,
    PROXMOX_CERTIFICATE_ANALYSIS,
    PROXMOX_GUEST_AGENT_ANALYSIS,
    PROXMOX_STORAGE_ANALYSIS,
    PROXMOX_SECURITY_ANALYSIS,
    PROXMOX_ONTOLOGY_LINKING,
)
