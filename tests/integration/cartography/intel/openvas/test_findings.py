"""
Integration tests for OpenVAS result (finding) and NVT sync.
"""

import cartography.intel.openvas.findings
import cartography.intel.openvas.hosts
import cartography.intel.openvas.tasks
from tests.data.openvas.responses import INSTANCE_ID
from tests.data.openvas.responses import NVT_OID_1
from tests.data.openvas.responses import NVT_OID_2
from tests.data.openvas.responses import RESULT_ID_1
from tests.data.openvas.responses import RESULT_ID_2
from tests.data.openvas.responses import TASK_ID_1
from tests.data.openvas.responses import TASK_ID_2
from tests.integration.cartography.intel.openvas.util import common_job_parameters
from tests.integration.cartography.intel.openvas.util import FakeGmp
from tests.integration.cartography.intel.openvas.util import seed_instance
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _seed_related_nodes(neo4j_session):
    """Load the resources results relate to (hosts, tasks) plus a CVE node."""
    common = common_job_parameters()
    cartography.intel.openvas.tasks.sync_tasks_and_supporting(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common,
    )
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common,
    )
    # Prerequisite setup: the CVE node the NVT exposes.
    neo4j_session.run("MERGE (c:CVE {id: 'CVE-2024-1000'})")


def _sync_results(neo4j_session, gmp=None, lookback_days=180):
    cartography.intel.openvas.findings.sync_results(
        neo4j_session,
        gmp or FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
        lookback_days=lookback_days,
    )


def test_sync_results(neo4j_session):
    """Results, deduped NVTs and their edges are loaded."""
    # Arrange
    seed_instance(neo4j_session)
    _seed_related_nodes(neo4j_session)

    # Act
    _sync_results(neo4j_session)

    # Assert
    result_nodes = (
        check_nodes(
            neo4j_session,
            "OpenVASResult",
            ["id", "host", "severity", "threat", "has_cve", "cve_id"],
        )
        or set()
    )
    assert (
        RESULT_ID_1,
        "10.0.0.5",
        7.5,
        "High",
        "true",
        "CVE-2024-1000",
    ) in result_nodes
    assert (RESULT_ID_2, "10.0.0.6", 0.0, "Log", "false", None) in result_nodes

    # Only detected NVTs are ingested, deduped by OID.
    nvt_nodes = check_nodes(neo4j_session, "OpenVASNVT", ["id", "oid"]) or set()
    assert (NVT_OID_1, NVT_OID_1) in nvt_nodes
    assert (NVT_OID_2, NVT_OID_2) in nvt_nodes
    assert len(nvt_nodes) == 2

    # Results with a CVE carry the CVE semantic label.
    cve_labeled = check_nodes(neo4j_session, "CVE", ["id"]) or set()
    assert (RESULT_ID_1,) in cve_labeled
    assert (RESULT_ID_2,) not in cve_labeled

    # NVTs link to the CVE nodes they expose.
    check_rels(
        neo4j_session,
        "OpenVASNVT",
        "id",
        "CVE",
        "id",
        "HAS_CVE",
        rel_direction_right=True,
    )

    # Results link to host, nvt and task.
    check_rels(
        neo4j_session,
        "OpenVASResult",
        "id",
        "OpenVASHost",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    )
    check_rels(
        neo4j_session,
        "OpenVASResult",
        "id",
        "OpenVASNVT",
        "id",
        "DETECTED_BY",
        rel_direction_right=True,
    )
    rels = (
        check_rels(
            neo4j_session,
            "OpenVASResult",
            "id",
            "OpenVASTask",
            "id",
            "PART_OF_SCAN",
            rel_direction_right=True,
        )
        or set()
    )
    assert (RESULT_ID_1, TASK_ID_1) in rels
    assert (RESULT_ID_2, TASK_ID_2) in rels


def test_sync_results_filters_by_lookback(neo4j_session):
    """The results fetch is restricted to the lookback window."""
    # Arrange
    seed_instance(neo4j_session)
    gmp = FakeGmp()

    # Act
    _sync_results(neo4j_session, gmp=gmp, lookback_days=30)

    # Assert
    results_call = gmp.calls["get_results"]
    assert len(results_call) == 1
    filter_string = results_call[0].get("filter_string")
    assert filter_string is not None
    assert "created>" in filter_string


def test_sync_results_cleanup_stale(neo4j_session):
    """Results not seen in a newer sync are removed scoped to the instance."""
    # Arrange
    seed_instance(neo4j_session)

    # Act
    _sync_results(neo4j_session)
    stale_gmp = FakeGmp()
    stale_gmp._responses["get_results"] = (
        '<get_results_response status="200" status_text="OK">'
        '<result_count full="1" truncated="0">0</result_count>'
        "</get_results_response>"
    )
    cartography.intel.openvas.findings.sync_results(
        neo4j_session,
        stale_gmp,
        INSTANCE_ID,
        TEST_UPDATE_TAG + 1,
        {**common_job_parameters(), "UPDATE_TAG": TEST_UPDATE_TAG + 1},
        lookback_days=180,
    )

    # Assert
    assert not check_nodes(neo4j_session, "OpenVASResult", ["id"])
