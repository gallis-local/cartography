"""
Integration tests for the OpenVAS entry point.
"""

import cartography.intel.openvas
from tests.data.openvas.responses import INSTANCE_ID
from tests.data.openvas.responses import NVT_OID_1
from tests.data.openvas.responses import RESULT_ID_1
from tests.data.openvas.responses import TASK_ID_1
from tests.data.openvas.responses import TASK_ID_2
from tests.integration.cartography.intel.openvas.util import gmp_session_fixture
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_start_openvas_ingestion_skips_without_password(neo4j_session, mocker):
    """The entry point is a no-op when no password is configured."""
    # Arrange
    config = mocker.MagicMock()
    config.openvas_password = None

    # Act
    cartography.intel.openvas.start_openvas_ingestion(neo4j_session, config)

    # Assert
    assert not check_nodes(neo4j_session, "OpenVASInstance", ["id"])


def test_start_openvas_ingestion(neo4j_session, mocker):
    """The entry point loads the instance node and syncs every domain."""
    # Arrange
    mocker.patch(
        "cartography.intel.openvas.gmp_session",
        return_value=gmp_session_fixture(),
    )
    config = mocker.MagicMock()
    config.openvas_password = "secret"
    config.openvas_instance_id = None
    config.openvas_socket_path = None
    config.openvas_host = "gvm.example.com"
    config.openvas_port = 9390
    config.openvas_user = "admin"
    config.openvas_findings_lookback_days = 180
    config.update_tag = TEST_UPDATE_TAG

    # Act
    cartography.intel.openvas.start_openvas_ingestion(neo4j_session, config)

    # Assert
    instance_nodes = (
        check_nodes(
            neo4j_session,
            "OpenVASInstance",
            ["id", "host", "port", "user"],
        )
        or set()
    )
    assert (INSTANCE_ID, "gvm.example.com", "9390", "admin") in instance_nodes

    assert ("10.0.0.5",) in (check_nodes(neo4j_session, "OpenVASHost", ["id"]) or set())
    assert (TASK_ID_1,) in (check_nodes(neo4j_session, "OpenVASTask", ["id"]) or set())
    assert (RESULT_ID_1,) in (
        check_nodes(neo4j_session, "OpenVASResult", ["id"]) or set()
    )
    assert (NVT_OID_1,) in (check_nodes(neo4j_session, "OpenVASNVT", ["id"]) or set())

    # get_assets carries no latest-scan reference, so the typed analysis job
    # derives it from each host's most recent result.
    latest = (
        check_nodes(
            neo4j_session,
            "OpenVASHost",
            ["id", "latest_scan_date", "latest_scan_task_id"],
        )
        or set()
    )
    assert (
        "10.0.0.5",
        "2024-06-01T12:05:00+00:00",
        TASK_ID_1,
    ) in latest
    assert (
        "10.0.0.6",
        "2024-06-02T10:00:00+00:00",
        TASK_ID_2,
    ) in latest

    rels = (
        check_rels(
            neo4j_session,
            "OpenVASHost",
            "id",
            "OpenVASTask",
            "id",
            "LAST_SCANNED_BY",
            rel_direction_right=True,
        )
        or set()
    )
    assert rels == {("10.0.0.5", TASK_ID_1), ("10.0.0.6", TASK_ID_2)}
