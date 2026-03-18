from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.sites
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
    common_job_parameters = {"UPDATE_TAG": 123456789, "site_id": "default"}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, common_job_parameters
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
    common_job_parameters = {"UPDATE_TAG": 123456789, "site_id": "default"}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, common_job_parameters
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
    # First load the site using the actual load function
    cartography.intel.unifi.sites.load_sites(
        neo4j_session,
        tests.data.unifi.UNIFI_SITES,
        123456789,
    )

    common_job_parameters = {"UPDATE_TAG": 123456789, "site_id": "default"}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, common_job_parameters
    )

    # Verify the relationship
    result = neo4j_session.run(
        """
        MATCH (s:UnifiSite{id: 'default'})-[:RESOURCE]->(w:UnifiWlan)
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
    # Site must exist so that the scoped cleanup query
    # MATCH (n:UnifiWlan)<-[:RESOURCE]-(:UnifiSite{id:$site_id}) can find nodes to delete.
    cartography.intel.unifi.sites.load_sites(
        neo4j_session, tests.data.unifi.UNIFI_SITES, 123456789
    )

    # First sync
    common_job_parameters = {"UPDATE_TAG": 123456789, "site_id": "default"}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, common_job_parameters
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
    common_job_parameters = {"UPDATE_TAG": 987654321, "site_id": "default"}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, None, common_job_parameters
    )

    # Verify WLANs were cleaned up
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan)
        RETURN count(w) AS count
        """
    )
    assert result.single()["count"] == 0


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.wlans,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_WLANS,
)
async def test_wlan_new_properties(mock_get, neo4j_session):
    """
    Test that new WLAN properties (mac_filter_policy, bc_filter_enabled, wlangroup_id, etc.) are stored.
    """
    common_job_parameters = {"UPDATE_TAG": 123456789, "site_id": "default"}
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, MagicMock(), common_job_parameters
    )

    # Corporate WiFi
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan {id: 'wlan_001'})
        RETURN w.mac_filter_policy AS policy, w.bc_filter_enabled AS bc,
               w.wlangroup_id AS wlangroup_id, w.name_combine_enabled AS name_combine
        """
    ).data()
    assert len(result) == 1
    assert result[0]["policy"] == "allow"
    assert result[0]["bc"] is False
    assert result[0]["wlangroup_id"] == "wlangroup_001"
    assert result[0]["name_combine"] is True

    # Guest WiFi — schedule should be stored
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan {id: 'wlan_002'})
        RETURN w.schedule AS schedule, w.no2ghz_oui AS no2ghz_oui
        """
    ).data()
    assert len(result) == 1
    assert result[0]["schedule"] == ["sun", "sat"]
    assert result[0]["no2ghz_oui"] is True
