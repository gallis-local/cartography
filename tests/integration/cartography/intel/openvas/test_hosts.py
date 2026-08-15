"""
Integration tests for OpenVAS host sync.
"""

import cartography.intel.openvas.hosts
from tests.data.openvas.responses import HOST_ID_1
from tests.data.openvas.responses import HOST_ID_2
from tests.data.openvas.responses import INSTANCE_ID
from tests.integration.cartography.intel.openvas.util import common_job_parameters
from tests.integration.cartography.intel.openvas.util import FakeGmp
from tests.integration.cartography.intel.openvas.util import seed_instance
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_sync_hosts(neo4j_session):
    """Hosts are loaded with their properties, labels and relationships."""
    # Arrange
    seed_instance(neo4j_session)

    # Act
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert
    nodes = (
        check_nodes(
            neo4j_session,
            "OpenVASHost",
            ["id", "ip", "hostname", "os", "severity", "latest_scan_task_id"],
        )
        or set()
    )
    assert (
        HOST_ID_1,
        "10.0.0.5",
        "web-01.example.com",
        "Linux",
        8.1,
        None,
    ) in nodes
    assert (HOST_ID_2, "10.0.0.6", None, None, 0.0, None) in nodes

    # Hosts carry the DEVICE_INSTANCE semantic label.
    device_nodes = check_nodes(neo4j_session, "DeviceInstance", ["id"]) or set()
    assert (HOST_ID_1,) in device_nodes

    check_rels(
        neo4j_session,
        "OpenVASInstance",
        "id",
        "OpenVASHost",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )


def test_sync_hosts_cleanup_stale(neo4j_session):
    """Hosts not seen in a newer sync are removed scoped to the instance."""
    # Arrange
    seed_instance(neo4j_session)

    # Act
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )
    stale_gmp = FakeGmp()
    # A sync with no hosts returned: both hosts must be cleaned up.
    stale_gmp._responses["get_hosts"] = (
        '<get_assets_response status="200" status_text="OK">'
        "<asset_count>0<filtered>0</filtered></asset_count>"
        "</get_assets_response>"
    )
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        stale_gmp,
        INSTANCE_ID,
        TEST_UPDATE_TAG_2,
        {**common_job_parameters(), "UPDATE_TAG": TEST_UPDATE_TAG_2},
    )

    # Assert
    assert not check_nodes(neo4j_session, "OpenVASHost", ["id"])
