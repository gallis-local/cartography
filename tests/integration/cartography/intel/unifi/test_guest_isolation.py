import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import cartography.intel.unifi.wlans
import cartography.intel.unifi.firewall_zones
import cartography.intel.unifi.firewall_policies
import cartography.intel.unifi.vouchers
import cartography.intel.unifi.clients
import cartography.intel.unifi.sites
import tests.data.unifi

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.wlans,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_WLANS,
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
@patch.object(
    cartography.intel.unifi.vouchers,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_VOUCHERS,
)
@patch.object(
    cartography.intel.unifi.clients,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_CLIENTS,
)
async def test_guest_isolation_analysis(
    mock_clients,
    mock_vouchers,
    mock_fw_policies,
    mock_fw_zones,
    mock_wlans,
    neo4j_session,
):
    """
    Test that guest network isolation analysis correctly identifies guest WLAN isolation status.
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
    await cartography.intel.unifi.firewall_zones.sync(
        neo4j_session, mock_controller, common_job_parameters
    )
    await cartography.intel.unifi.firewall_policies.sync(
        neo4j_session, mock_controller, common_job_parameters
    )
    await cartography.intel.unifi.vouchers.sync(
        neo4j_session, mock_controller, common_job_parameters
    )
    await cartography.intel.unifi.clients.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Run analysis job directly
    from cartography.util import run_analysis_job

    run_analysis_job(
        "unifi_guest_isolation.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Guest WiFi (wlan_002) should be marked as guest_isolated=true but have issues
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan {id: 'wlan_002'})
        RETURN w.guest_isolated as isolated, w.guest_isolation_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["isolated"] is True
    assert "open_security" in result[0]["issues"]
    assert "no_mac_filter" in result[0]["issues"]

    # Assert - Corporate WiFi (wlan_001) should NOT be marked as guest
    result = neo4j_session.run(
        """
        MATCH (w:UnifiWlan {id: 'wlan_001'})
        RETURN w.guest_isolated as isolated
        """
    ).data()

    assert len(result) == 1
    assert result[0]["isolated"] is None
