"""
Integration tests for OpenVAS task and supporting resource sync.
"""

import cartography.intel.openvas.tasks
from tests.data.openvas.responses import CONFIG_ID_1
from tests.data.openvas.responses import INSTANCE_ID
from tests.data.openvas.responses import PORT_LIST_ID_1
from tests.data.openvas.responses import SCHEDULE_ID_1
from tests.data.openvas.responses import SMB_CRED_ID_1
from tests.data.openvas.responses import SSH_CRED_ID_1
from tests.data.openvas.responses import TARGET_ID_1
from tests.data.openvas.responses import TASK_ID_1
from tests.integration.cartography.intel.openvas.util import common_job_parameters
from tests.integration.cartography.intel.openvas.util import FakeGmp
from tests.integration.cartography.intel.openvas.util import seed_instance
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_sync_tasks_and_supporting(neo4j_session):
    """Tasks and their supporting resources are loaded with their edges."""
    # Arrange
    seed_instance(neo4j_session)

    # Act
    cartography.intel.openvas.tasks.sync_tasks_and_supporting(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert
    task_nodes = (
        check_nodes(
            neo4j_session,
            "OpenVASTask",
            [
                "id",
                "status",
                "last_report_id",
                "last_report_timestamp",
                "last_report_scan_start",
                "last_report_scan_end",
            ],
        )
        or set()
    )
    assert (
        TASK_ID_1,
        "Done",
        "report-1",
        "2024-06-01T12:00:00+00:00",
        "2024-06-01T10:00:00+00:00",
        "2024-06-01T12:00:00+00:00",
    ) in task_nodes

    target_nodes = check_nodes(neo4j_session, "OpenVASTarget", ["id", "hosts"]) or set()
    assert (TARGET_ID_1, "10.0.0.0/24") in target_nodes

    config_nodes = check_nodes(neo4j_session, "OpenVASConfig", ["id"]) or set()
    assert (CONFIG_ID_1,) in config_nodes

    schedule_nodes = check_nodes(neo4j_session, "OpenVASSchedule", ["id"]) or set()
    assert (SCHEDULE_ID_1,) in schedule_nodes

    port_list_nodes = check_nodes(neo4j_session, "OpenVASPortList", ["id"]) or set()
    assert (PORT_LIST_ID_1,) in port_list_nodes

    credential_nodes = check_nodes(neo4j_session, "OpenVASCredential", ["id"]) or set()
    assert (SSH_CRED_ID_1,) in credential_nodes
    assert (SMB_CRED_ID_1,) in credential_nodes

    # Every resource points RESOURCE at the instance.
    for label in (
        "OpenVASTask",
        "OpenVASTarget",
        "OpenVASConfig",
        "OpenVASSchedule",
        "OpenVASPortList",
        "OpenVASCredential",
    ):
        rels = (
            check_rels(
                neo4j_session,
                "OpenVASInstance",
                "id",
                label,
                "id",
                "RESOURCE",
                rel_direction_right=True,
            )
            or set()
        )
        assert rels, f"Missing RESOURCE edge from instance to {label}"

    check_rels(
        neo4j_session,
        "OpenVASTask",
        "id",
        "OpenVASTarget",
        "id",
        "SCANS",
        rel_direction_right=True,
    )
    check_rels(
        neo4j_session,
        "OpenVASTask",
        "id",
        "OpenVASConfig",
        "id",
        "USES",
        rel_direction_right=True,
    )
    check_rels(
        neo4j_session,
        "OpenVASTask",
        "id",
        "OpenVASSchedule",
        "id",
        "USES",
        rel_direction_right=True,
    )
    check_rels(
        neo4j_session,
        "OpenVASTarget",
        "id",
        "OpenVASPortList",
        "id",
        "USES",
        rel_direction_right=True,
    )
    check_rels(
        neo4j_session,
        "OpenVASTarget",
        "id",
        "OpenVASCredential",
        "id",
        "USES_SSH_CREDENTIAL",
        rel_direction_right=True,
    )
    check_rels(
        neo4j_session,
        "OpenVASTarget",
        "id",
        "OpenVASCredential",
        "id",
        "USES_SMB_CREDENTIAL",
        rel_direction_right=True,
    )
