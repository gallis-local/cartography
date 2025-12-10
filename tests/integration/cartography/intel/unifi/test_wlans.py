from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.wlans
import tests.data.unifi


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.wlans,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_WLANS,
)
async def test_load_unifi_wlans(mock_get, neo4j_session):
    """
    Test that we can load UniFi WLANs into Neo4j.
    """
    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, "default", common_job_parameters
    )

    # Verify the WLANs were loaded
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan)
        RETURN w.id AS id, w.name AS name, w.is_guest AS is_guest
        ORDER BY w.id
        """
    )
    records = list(result)
    assert len(records) == 2

    # Check Corporate WiFi
    assert records[0]["id"] == "wlan_001"
    assert records[0]["name"] == "Corporate WiFi"
    assert records[0]["is_guest"] is False

    # Check Guest WiFi
    assert records[1]["id"] == "wlan_002"
    assert records[1]["name"] == "Guest WiFi"
    assert records[1]["is_guest"] is True


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.wlans,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_WLANS,
)
async def test_wlan_properties(mock_get, neo4j_session):
    """
    Test that WLAN properties are loaded correctly.
    """
    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, "default", common_job_parameters
    )

    # Check corporate WLAN security properties
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan{id: 'wlan_001'})
        RETURN w.security AS security, w.wpa_mode AS wpa_mode,
               w.enabled AS enabled, w.hide_ssid AS hide_ssid
        """
    )
    record = result.single()
    assert record["security"] == "wpapsk"
    assert record["wpa_mode"] == "wpa2"
    assert record["enabled"] is True
    assert record["hide_ssid"] is False


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.wlans,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_WLANS,
)
async def test_wlan_to_site_relationship(mock_get, neo4j_session):
    """
    Test that WLANs are correctly linked to their site.
    """
    # First load the site
    neo4j_session.run(
        """
        MERGE (s:UnifiSite{id: 'default'})
        SET s.name = 'Default', s.lastupdated = 123456789
        """
    )

    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, "default", common_job_parameters
    )

    # Verify the relationship
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan)-[:RESOURCE]->(s:UnifiSite{id: 'default'})
        RETURN count(w) AS count
        """
    )
    assert result.single()["count"] == 2


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.wlans,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_WLANS,
)
async def test_cleanup_unifi_wlans(mock_get, neo4j_session):
    """
    Test that stale UniFi WLANs are cleaned up.
    """
    # First sync
    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, "default", common_job_parameters
    )

    # Verify WLANs exist
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan)
        RETURN count(w) AS count
        """
    )
    assert result.single()["count"] == 2

    # Second sync with a new update tag (simulating WLAN removal)
    mock_get.return_value = []
    common_job_parameters = {"UPDATE_TAG": 987654321}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, "default", common_job_parameters
    )

    # Verify WLANs were cleaned up
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan)
        RETURN count(w) AS count
        """
    )
    assert result.single()["count"] == 0
