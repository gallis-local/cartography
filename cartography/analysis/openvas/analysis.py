"""
Typed analysis jobs for the OpenVAS module.
"""

from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import Var

# GVM's asset management (get_assets) reports no latest-scan or task reference
# for a host, so the host sync cannot fill these in. The information does exist
# in the graph: every OpenVASResult carries its creation time and the task run
# that produced it. Deriving the host's most recent scan here is what makes
# "when was this host last looked at, and by which scan?" answerable -- and, just
# as importantly, makes a host that has stopped being scanned visible.
OPENVAS_HOST_LATEST_SCAN = AnalysisJob(
    name="OpenVAS host latest scan",
    short_name="openvas_host_latest_scan",
    scope=ScopeById(
        "OpenVASInstance",
        "OPENVAS_INSTANCE_ID",
        scope_on="h",
    ),
    statements=(
        AnalysisStatement(
            comment="Set each host's latest scan from its most recent result.",
            match=(
                "MATCH (h:OpenVASHost)<-[:AFFECTS]-(r:OpenVASResult)"
                "-[:PART_OF_SCAN]->(t:OpenVASTask) "
                "WHERE r.created IS NOT NULL "
                # GMP timestamps are ISO-8601 with a fixed offset per gvmd, so a
                # lexical sort is a chronological sort here.
                "WITH h, r, t ORDER BY r.created DESC "
                "WITH h, head(collect({created: r.created, task: t})) AS latest "
                "WITH h, latest.task AS t, latest.created AS latest_scan_date"
            ),
            effects=(
                SetProperties(
                    "h",
                    {
                        "latest_scan_date": Var("latest_scan_date"),
                        "latest_scan_task_id": Var("t.id"),
                        "latest_scan_task_name": Var("t.name"),
                    },
                    label="OpenVASHost",
                ),
                AddRelationship(
                    "h",
                    "LAST_SCANNED_BY",
                    "t",
                    source_label="OpenVASHost",
                    target_label="OpenVASTask",
                ),
            ),
        ),
    ),
)

OPENVAS_ANALYSIS_JOBS = (OPENVAS_HOST_LATEST_SCAN,)
