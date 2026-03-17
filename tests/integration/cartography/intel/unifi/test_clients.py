from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.clients
import cartography.intel.unifi.ports
import cartography.intel.unifi.sites
import cartography.intel.unifi.wlans
import tests.data.unifi
from tests.integration.cartography.intel.unifi.test_devices import (
    _ensure_local_neo4j_has_test_devices,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_sites(neo4j_session):
    """Load test UniFi sites into Neo4j."""
    cartography.intel.unifi.sites.load_sites(
        neo4j_session,
        tests.data.unifi.UNIFI_SITES,
        TEST_UPDATE_TAG,
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_load_unifi_clients(mock_get, neo4j_session):
    """
    Ensure that UniFi clients actually get loaded.
    """
    # Arrange - First load sites and devices that clients will connect to
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    _ensure_local_neo4j_has_test_devices(neo4j_session)

    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.clients.sync(
        neo4j_session,
        mock_controller,
        common_job_parameters,
    )

    # Assert - Check that clients were loaded
    expected_nodes = {
        ("11:22:33:44:55:66", "192.168.1.100"),
        ("77:88:99:AA:BB:CC", "192.168.1.101"),
        ("DD:EE:FF:00:11:22", "192.168.1.102"),
    }
    assert check_nodes(neo4j_session, "UnifiClient", ["id", "ip"]) == expected_nodes


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_unifi_clients_to_device_relationships(mock_get, neo4j_session):
    """
    Ensure that UniFi clients are correctly linked to their devices.
    """
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    # Arrange - Load devices first
    _ensure_local_neo4j_has_test_devices(neo4j_session)

    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.clients.sync(
        neo4j_session,
        mock_controller,
        common_job_parameters,
    )

    # Assert - Wireless clients connected to Office AP via CONNECTED_TO_AP
    expected_wireless_rels = {
        ("11:22:33:44:55:66", "00:11:22:33:44:55"),
        ("77:88:99:AA:BB:CC", "00:11:22:33:44:55"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiClient",
            "id",
            "UnifiDevice",
            "id",
            "CONNECTED_TO_AP",
            rel_direction_right=False,
        )
        == expected_wireless_rels
    )

    # Assert - All clients reach the switch via CONNECTED_TO_SWITCH:
    # wired client directly, wireless clients via their AP's uplink
    expected_switch_rels = {
        ("11:22:33:44:55:66", "AA:BB:CC:DD:EE:FF"),  # iPhone via AP uplink
        ("77:88:99:AA:BB:CC", "AA:BB:CC:DD:EE:FF"),  # Samsung via AP uplink
        ("DD:EE:FF:00:11:22", "AA:BB:CC:DD:EE:FF"),  # Dell wired directly
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiClient",
            "id",
            "UnifiDevice",
            "id",
            "CONNECTED_TO_SWITCH",
            rel_direction_right=False,
        )
        == expected_switch_rels
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_unifi_clients_properties(mock_get, neo4j_session):
    """
    Ensure that UniFi clients have all expected properties.
    """
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    # Arrange
    _ensure_local_neo4j_has_test_devices(neo4j_session)

    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.clients.sync(
        neo4j_session,
        mock_controller,
        common_job_parameters,
    )

    # Assert - Check wireless client properties
    wireless_client = neo4j_session.run(
        """
        MATCH (c:UnifiClient {id: '11:22:33:44:55:66'})
        RETURN c.is_guest as is_guest, c.is_wired as is_wired,
               c.satisfaction as satisfaction, c.oui as oui
        """
    ).data()

    assert len(wireless_client) == 1
    assert wireless_client[0]["is_guest"] is False
    assert wireless_client[0]["is_wired"] is False
    assert wireless_client[0]["satisfaction"] == 98
    assert wireless_client[0]["oui"] == "Apple"

    # Assert - Check wired client properties
    wired_client = neo4j_session.run(
        """
        MATCH (c:UnifiClient {id: 'DD:EE:FF:00:11:22'})
        RETURN c.is_wired as is_wired, c.oui as oui
        """
    ).data()

    assert len(wired_client) == 1
    assert wired_client[0]["is_wired"] is True
    assert wired_client[0]["oui"] == "Dell"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_unifi_clients_cleanup(mock_get, neo4j_session):
    """
    Ensure that disconnected clients are cleaned up.
    """
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    # Arrange - Load devices and initial clients
    _ensure_local_neo4j_has_test_devices(neo4j_session)

    old_update_tag = 111111111
    disconnected_client = [
        {
            "mac": "99:99:99:99:99:99",
            "ip": "192.168.1.200",
            "is_guest": False,
            "oui": "Unknown",
            "satisfaction": 50,
            "channel": 1,
            "radio": "ng",
            "is_wired": False,
            "qos_policy_applied": False,
            "ap_mac": "00:11:22:33:44:55",
            "hostname": None,
            "name": None,
            "essid": None,
            "blocked": False,
            "uptime": 0,
            "last_seen": None,
            "vlan": None,
            "sw_mac": None,
            "sw_port": None,
            "port_id": None,
            "ap_switch_mac": None,
            "site_id": "default",
        }
    ]
    cartography.intel.unifi.clients.load_clients(
        neo4j_session,
        disconnected_client,
        "default",  # site_id
        old_update_tag,
    )

    # Act - Sync with new data (disconnected client not present)
    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }
    await cartography.intel.unifi.clients.sync(
        neo4j_session,
        mock_controller,
        common_job_parameters,
    )

    # Assert - Disconnected client should be removed
    nodes = neo4j_session.run(
        """
        MATCH (c:UnifiClient {id: '99:99:99:99:99:99'})
        RETURN c
        """
    ).data()
    assert len(nodes) == 0

    # Assert - Current clients should still exist
    current_nodes = neo4j_session.run(
        """
        MATCH (c:UnifiClient)
        WHERE c.lastupdated = $update_tag
        RETURN c.id as id
        """,
        update_tag=TEST_UPDATE_TAG,
    ).data()
    assert len(current_nodes) == 3


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_unifi_guest_vs_regular_clients(mock_get, neo4j_session):
    """
    Ensure that guest and regular clients are properly distinguished.
    """
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    # Arrange
    _ensure_local_neo4j_has_test_devices(neo4j_session)

    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.clients.sync(
        neo4j_session,
        mock_controller,
        common_job_parameters,
    )

    # Assert - Count guest clients
    guest_count = neo4j_session.run(
        """
        MATCH (c:UnifiClient {is_guest: true})
        RETURN count(c) as count
        """
    ).data()[0]["count"]
    assert guest_count == 1

    # Assert - Count regular clients
    regular_count = neo4j_session.run(
        """
        MATCH (c:UnifiClient {is_guest: false})
        RETURN count(c) as count
        """
    ).data()[0]["count"]
    assert regular_count == 2


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_unifi_client_new_properties(mock_get, neo4j_session):
    """
    Ensure that new client properties (hostname, essid, blocked, uptime, etc.) are stored.
    """
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    _ensure_local_neo4j_has_test_devices(neo4j_session)
    mock_controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.clients.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Wireless client
    result = neo4j_session.run(
        """
        MATCH (c:UnifiClient {id: '11:22:33:44:55:66'})
        RETURN c.hostname as hostname, c.essid as essid,
               c.blocked as blocked, c.uptime as uptime
        """
    ).data()
    assert len(result) == 1
    assert result[0]["hostname"] == "iphone-office"
    assert result[0]["essid"] == "Corporate WiFi"
    assert result[0]["blocked"] is False
    assert result[0]["uptime"] == 3600

    # Wired client
    wired = neo4j_session.run(
        """
        MATCH (c:UnifiClient {id: 'DD:EE:FF:00:11:22'})
        RETURN c.sw_mac as sw_mac, c.sw_port as sw_port, c.vlan as vlan
        """
    ).data()
    assert len(wired) == 1
    assert wired[0]["sw_mac"] == "AA:BB:CC:DD:EE:FF"
    assert wired[0]["sw_port"] == 1
    assert wired[0]["vlan"] == 10


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_unifi_wireless_client_to_switch_relationships(mock_get, neo4j_session):
    """
    Ensure that wireless clients are linked to the switch their AP uplinks through
    via CONNECTED_TO_SWITCH, the same relationship used by wired clients.
    This allows querying all clients on a switch with a single relationship type.
    """
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    _ensure_local_neo4j_has_test_devices(neo4j_session)
    mock_controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.clients.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Both wireless clients reach the switch via their AP's uplink
    expected_rels = {
        ("11:22:33:44:55:66", "AA:BB:CC:DD:EE:FF"),  # iPhone -> switch (via AP)
        ("77:88:99:AA:BB:CC", "AA:BB:CC:DD:EE:FF"),  # Samsung -> switch (via AP)
        ("DD:EE:FF:00:11:22", "AA:BB:CC:DD:EE:FF"),  # Dell -> switch (direct, wired)
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiClient",
            "id",
            "UnifiDevice",
            "id",
            "CONNECTED_TO_SWITCH",
            rel_direction_right=False,
        )
        == expected_rels
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_unifi_client_to_wlan_relationships(mock_get, neo4j_session):
    """
    Ensure that wireless clients are linked to their WLANs via CONNECTED_TO_WLAN.
    """
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    _ensure_local_neo4j_has_test_devices(neo4j_session)
    # Load WLANs first so the relationship can be established
    cartography.intel.unifi.wlans.load_wlans(
        neo4j_session, tests.data.unifi.UNIFI_WLANS, "default", TEST_UPDATE_TAG
    )
    mock_controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.clients.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    expected_rels = {
        ("11:22:33:44:55:66", "wlan_001"),  # iPhone -> Corporate WiFi
        ("77:88:99:AA:BB:CC", "wlan_002"),  # Samsung -> Guest WiFi
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiClient",
            "id",
            "UnifiWlan",
            "id",
            "CONNECTED_TO_WLAN",
            rel_direction_right=False,
        )
        == expected_rels
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_CLIENTS, "default"),
)
async def test_unifi_wired_client_to_port_relationships(mock_get, neo4j_session):
    """
    Ensure that wired clients are linked to their switch ports via CONNECTED_VIA.
    """
    _ensure_local_neo4j_has_test_sites(neo4j_session)
    _ensure_local_neo4j_has_test_devices(neo4j_session)
    # Load ports first so the relationship can be established
    cartography.intel.unifi.ports.load_ports(
        neo4j_session, tests.data.unifi.UNIFI_PORTS, "default", TEST_UPDATE_TAG
    )
    mock_controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.clients.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Wired client connects via port AA:BB:CC:DD:EE:FF_1
    expected_rels = {
        ("DD:EE:FF:00:11:22", "AA:BB:CC:DD:EE:FF_1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiClient",
            "id",
            "UnifiPort",
            "id",
            "CONNECTED_VIA",
            rel_direction_right=False,
        )
        == expected_rels
    )
