import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import cartography.intel.unifi.devices
import cartography.intel.unifi.wlans
import cartography.intel.unifi.port_forwards
import cartography.intel.unifi.firewall_zones
import cartography.intel.unifi.firewall_policies
import cartography.intel.unifi.sites
import tests.data.unifi
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DEVICES,
)
@patch.object(
    cartography.intel.unifi.wlans,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_WLANS,
)
@patch.object(
    cartography.intel.unifi.port_forwards,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_PORT_FORWARDS,
)
@patch.object(
    cartography.intel.unifi.firewall_zones,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_FIREWALL_ZONES,
)
@patch.object(
    cartography.intel.unifi.firewall_policies,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_FIREWALL_POLICIES,
)
async def test_internet_exposure_analysis(
    mock_fw_policies, mock_fw_zones, mock_pf, mock_wlans, mock_devices, neo4j_session
):
    """
    Test that internet exposure analysis correctly marks exposed devices, WLANs, and port forwards.
    """
    # Arrange
    mock_controller = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "site_id": "default",
    }

    # Load prerequisite data
    cartography.intel.unifi.sites.load_sites(
        neo4j_session, tests.data.unifi.UNIFI_SITES, TEST_UPDATE_TAG
    )

    # Act - sync all required modules
    await cartography.intel.unifi.wlans.sync(
        neo4j_session, mock_controller, common_job_parameters
    )
    await cartography.intel.unifi.devices.sync(
        neo4j_session, mock_controller, common_job_parameters
    )
    await cartography.intel.unifi.port_forwards.sync(
        neo4j_session, mock_controller, common_job_parameters
    )
    await cartography.intel.unifi.firewall_zones.sync(
        neo4j_session, mock_controller, common_job_parameters
    )
    await cartography.intel.unifi.firewall_policies.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Run analysis job directly
    from cartography.util import run_analysis_job

    run_analysis_job(
        "unifi_internet_exposure.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Check that device with WAN IP is marked as exposed
    result = neo4j_session.run(
        """
        MATCH (d:UnifiDevice {id: 'AA:BB:CC:DD:EE:FF'})
        RETURN d.exposed_internet as exposed, d.exposed_internet_type as types
        """
    ).data()

    assert len(result) == 1
    assert result[0]["exposed"] is True
    assert "wan_ip" in result[0]["types"]

    # Assert - Check that enabled port forward is marked as exposed
    result = neo4j_session.run(
        """
        MATCH (pf:UnifiPortForward {id: 'pf_001'})
        RETURN pf.exposed_internet as exposed, pf.exposed_internet_type as types
        """
    ).data()

    assert len(result) == 1
    assert result[0]["exposed"] is True
    assert "port_forward" in result[0]["types"]

    # Assert - Check that open guest WLAN is marked as exposed
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan {id: 'wlan_002'})
        RETURN w.exposed_internet as exposed, w.exposed_internet_type as types
        """
    ).data()

    assert len(result) == 1
    assert result[0]["exposed"] is True
    assert "guest_wlan" in result[0]["types"]

    # Assert - Check that disabled port forward is NOT marked as exposed
    result = neo4j_session.run(
        """
        MATCH (pf:UnifiPortForward {id: 'pf_002'})
        RETURN pf.exposed_internet as exposed
        """
    ).data()

    assert len(result) == 1
    assert result[0]["exposed"] is None
