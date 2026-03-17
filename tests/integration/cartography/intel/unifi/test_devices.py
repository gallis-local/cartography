from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.devices
import cartography.intel.unifi.ports
import cartography.intel.unifi.sites
import cartography.intel.unifi.wlans
import tests.data.unifi
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_devices(neo4j_session):
    """Load test UniFi devices into Neo4j."""
    cartography.intel.unifi.devices.load_devices(
        neo4j_session,
        tests.data.unifi.UNIFI_DEVICES,
        "default",  # site_id
        TEST_UPDATE_TAG,
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_DEVICES, "default"),
)
async def test_load_unifi_devices(mock_get, neo4j_session):
    """
    Ensure that UniFi devices actually get loaded.
    """
    # Arrange
    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.devices.sync(
        neo4j_session,
        mock_controller,
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


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_DEVICES, "default"),
)
async def test_unifi_devices_have_correct_properties(mock_get, neo4j_session):
    """
    Ensure that UniFi devices have all expected properties.
    """
    # Arrange
    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.devices.sync(
        neo4j_session,
        mock_controller,
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


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_DEVICES, "default"),
)
async def test_unifi_devices_cleanup(mock_get, neo4j_session):
    """
    Ensure that stale UniFi devices are cleaned up.
    """
    # Arrange - First load the site
    cartography.intel.unifi.sites.load_sites(
        neo4j_session,
        tests.data.unifi.UNIFI_SITES,
        111111111,
    )

    # Load devices with old update tag
    old_update_tag = 111111111
    cartography.intel.unifi.devices.load_devices(
        neo4j_session,
        tests.data.unifi.UNIFI_DEVICES,
        "default",  # site_id
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
            "ip": None,
            "version": None,
            "state": None,
            "uptime": 0,
            "last_seen": None,
            "upgradable": False,
            "uplink_mac": None,
            "uplink_port_id": None,
            "wlan_ids": None,
            "site_id": "default",
        }
    ]
    cartography.intel.unifi.devices.load_devices(
        neo4j_session,
        stale_device,
        "default",  # site_id
        old_update_tag,
    )

    # Act - Sync with new update tag (stale device not in new data)
    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }
    await cartography.intel.unifi.devices.sync(
        neo4j_session,
        mock_controller,
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


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_DEVICES, "default"),
)
async def test_unifi_device_new_properties(mock_get, neo4j_session):
    """
    Ensure that new device properties (ip, version, state, uptime, etc.) are stored.
    """
    mock_controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.devices.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    result = neo4j_session.run(
        """
        MATCH (d:UnifiDevice {id: '00:11:22:33:44:55'})
        RETURN d.ip as ip, d.version as version, d.state as state,
               d.uptime as uptime, d.upgradable as upgradable, d.uplink_mac as uplink_mac
        """
    ).data()

    assert len(result) == 1
    assert result[0]["ip"] == "192.168.1.2"
    assert result[0]["version"] == "6.5.28.14301"
    assert result[0]["state"] == "CONNECTED"
    assert result[0]["uptime"] == 86400
    assert result[0]["upgradable"] is False
    assert result[0]["uplink_mac"] == "AA:BB:CC:DD:EE:FF"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_DEVICES, "default"),
)
async def test_unifi_device_uplink_topology(mock_get, neo4j_session):
    """
    Ensure that UniFi device uplink topology relationships are created.
    The AP should have an UPLINK_TO relationship pointing to the switch.
    """
    cartography.intel.unifi.sites.load_sites(
        neo4j_session, tests.data.unifi.UNIFI_SITES, TEST_UPDATE_TAG
    )
    mock_controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.devices.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # AP uplinks to switch
    expected_rels = {
        ("00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiDevice",
            "id",
            "UnifiDevice",
            "id",
            "UPLINK_TO",
            rel_direction_right=False,
        )
        == expected_rels
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_DEVICES, "default"),
)
async def test_unifi_device_broadcasts_wlan(mock_get, neo4j_session):
    """
    Ensure that access points have BROADCASTS relationships to the WLANs they transmit.
    """
    cartography.intel.unifi.sites.load_sites(
        neo4j_session, tests.data.unifi.UNIFI_SITES, TEST_UPDATE_TAG
    )
    # Load WLANs first so the relationship can be resolved
    cartography.intel.unifi.wlans.load_wlans(
        neo4j_session, tests.data.unifi.UNIFI_WLANS, "default", TEST_UPDATE_TAG
    )
    mock_controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.devices.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Office AP broadcasts both Corporate WiFi and Guest WiFi
    expected_rels = {
        ("00:11:22:33:44:55", "wlan_001"),
        ("00:11:22:33:44:55", "wlan_002"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiDevice",
            "id",
            "UnifiWlan",
            "id",
            "BROADCASTS",
            rel_direction_right=True,
        )
        == expected_rels
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_DEVICES, "default"),
)
async def test_unifi_device_uplink_via_port(mock_get, neo4j_session):
    """
    Ensure that a device's uplink port relationship is created.
    The AP should have an UPLINK_VIA_PORT relationship pointing to the specific
    port on the upstream switch it connects through.
    """
    cartography.intel.unifi.sites.load_sites(
        neo4j_session, tests.data.unifi.UNIFI_SITES, TEST_UPDATE_TAG
    )
    # Load ports so the relationship target exists
    cartography.intel.unifi.ports.load_ports(
        neo4j_session, tests.data.unifi.UNIFI_PORTS, "default", TEST_UPDATE_TAG
    )
    mock_controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.devices.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # AP uplinks via switch port AA:BB:CC:DD:EE:FF_1
    expected_rels = {
        ("00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF_1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiDevice",
            "id",
            "UnifiPort",
            "id",
            "UPLINK_VIA_PORT",
            rel_direction_right=True,
        )
        == expected_rels
    )
