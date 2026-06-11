import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import cartography.intel.unifi.outlets
import cartography.intel.unifi.devices
import cartography.intel.unifi.sites
import tests.data.unifi

# Add outlet test data
UNIFI_OUTLETS = [
    {
        "id": "AA:BB:CC:DD:EE:FF_1",
        "name": "Outlet 1",
        "index": 1,
        "has_relay": True,
        "relay_state": True,
        "cycle_enabled": False,
        "has_metering": True,
        "caps": 3,
        "voltage": "120.5",
        "current": "2.5",
        "power": "300.0",
        "power_factor": "0.95",
        "device_mac": "AA:BB:CC:DD:EE:FF",
        "site_id": "default",
    },
    {
        "id": "AA:BB:CC:DD:EE:FF_2",
        "name": "Outlet 2",
        "index": 2,
        "has_relay": True,
        "relay_state": False,
        "cycle_enabled": False,
        "has_metering": True,
        "caps": 3,
        "voltage": "120.0",
        "current": "0.0",
        "power": "0.0",
        "power_factor": "1.0",
        "device_mac": "AA:BB:CC:DD:EE:FF",
        "site_id": "default",
    },
]

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.outlets,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_OUTLETS,
)
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DEVICES,
)
async def test_power_monitoring_analysis(mock_devices, mock_outlets, neo4j_session):
    """
    Test that power monitoring analysis correctly identifies outlet power issues.
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
    cartography.intel.unifi.devices.load_devices(
        neo4j_session, tests.data.unifi.UNIFI_DEVICES, "default", TEST_UPDATE_TAG
    )

    # Act - sync outlets
    await cartography.intel.unifi.outlets.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Run analysis job directly
    from cartography.util import run_analysis_job

    run_analysis_job(
        "unifi_power_monitoring.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Outlet 1 (on, metering, healthy power factor) should be healthy
    result = neo4j_session.run(
        """
        MATCH (o:UnifiOutlet {id: 'AA:BB:CC:DD:EE:FF_1'})
        RETURN o.power_status as status, o.power_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["status"] == "healthy"
    assert result[0]["issues"] in (None, [])

    # Assert - Outlet 2 (off, metering capable) should have warning
    result = neo4j_session.run(
        """
        MATCH (o:UnifiOutlet {id: 'AA:BB:CC:DD:EE:FF_2'})
        RETURN o.power_status as status, o.power_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["status"] == "warning"
    assert "outlet_off" in result[0]["issues"]
