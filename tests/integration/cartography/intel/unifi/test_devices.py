from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.unifi.devices
import tests.data.unifi
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_devices(neo4j_session):
    """Load test UniFi devices into Neo4j."""
    cartography.intel.unifi.devices.load_devices(
        neo4j_session,
        tests.data.unifi.UNIFI_DEVICES,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.unifi.devices,
    "get",
    return_value=tests.data.unifi.UNIFI_DEVICES,
)
def test_load_unifi_devices(mock_get, neo4j_session):
    """
    Ensure that UniFi devices actually get loaded.
    """
    # Arrange
    mock_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    cartography.intel.unifi.devices.sync(
        neo4j_session,
        mock_client,
        common_job_parameters,
    )

    # Assert - Check that devices were loaded with correct properties
    expected_nodes = {
        ("00:11:22:33:44:55", "Office AP", "U7PG2"),
        ("AA:BB:CC:DD:EE:FF", "Main Switch", "US24P250"),
    }
    assert (
        check_nodes(neo4j_session, "UnifiDevice", ["id", "name", "model"])
        == expected_nodes
    )


@patch.object(
    cartography.intel.unifi.devices,
    "get",
    return_value=tests.data.unifi.UNIFI_DEVICES,
)
def test_unifi_devices_have_correct_properties(mock_get, neo4j_session):
    """
    Ensure that UniFi devices have all expected properties.
    """
    # Arrange
    mock_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    cartography.intel.unifi.devices.sync(
        neo4j_session,
        mock_client,
        common_job_parameters,
    )

    # Assert - Verify device properties
    nodes = neo4j_session.run(
        """
        MATCH (d:UnifiDevice {id: '00:11:22:33:44:55'})
        RETURN d.mac as mac, d.adopted as adopted, d.type as type
        """
    ).data()

    assert len(nodes) == 1
    assert nodes[0]["mac"] == "00:11:22:33:44:55"
    assert nodes[0]["adopted"] is True
    assert nodes[0]["type"] == "uap"


@patch.object(
    cartography.intel.unifi.devices,
    "get",
    return_value=tests.data.unifi.UNIFI_DEVICES,
)
def test_unifi_devices_cleanup(mock_get, neo4j_session):
    """
    Ensure that stale UniFi devices are cleaned up.
    """
    # Arrange - Load devices with old update tag
    old_update_tag = 111111111
    cartography.intel.unifi.devices.load_devices(
        neo4j_session,
        tests.data.unifi.UNIFI_DEVICES,
        old_update_tag,
    )

    # Add a device that will become stale
    stale_device = [
        {
            "mac": "FF:FF:FF:FF:FF:FF",
            "adopted": True,
            "type": "uap",
            "model": "STALE",
            "name": "Stale Device",
        }
    ]
    cartography.intel.unifi.devices.load_devices(
        neo4j_session,
        stale_device,
        old_update_tag,
    )

    # Act - Sync with new update tag (stale device not in new data)
    mock_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }
    cartography.intel.unifi.devices.sync(
        neo4j_session,
        mock_client,
        common_job_parameters,
    )

    # Assert - Stale device should be removed
    nodes = neo4j_session.run(
        """
        MATCH (d:UnifiDevice {id: 'FF:FF:FF:FF:FF:FF'})
        RETURN d
        """
    ).data()
    assert len(nodes) == 0

    # Assert - Current devices should still exist
    current_nodes = neo4j_session.run(
        """
        MATCH (d:UnifiDevice)
        WHERE d.lastupdated = $update_tag
        RETURN d.id as id
        """,
        update_tag=TEST_UPDATE_TAG,
    ).data()
    assert len(current_nodes) == 2
