import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import cartography.intel.unifi.devices
import cartography.intel.unifi.sites
import tests.data.unifi

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DEVICES,
)
async def test_device_health_analysis(mock_devices, neo4j_session):
    """
    Test that device health analysis correctly calculates health scores.
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

    # Act - sync devices
    await cartography.intel.unifi.devices.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Run analysis job directly
    from cartography.util import run_analysis_job

    run_analysis_job(
        "unifi_device_health.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Office AP should have health_score = 100 (no issues)
    result = neo4j_session.run(
        """
        MATCH (d:UnifiDevice {id: '00:11:22:33:44:55'})
        RETURN d.health_score as score, d.health_issues as issues, d.temperature_status as temp, d.power_status as power
        """
    ).data()

    assert len(result) == 1
    assert result[0]["score"] == 100
    assert result[0]["issues"] in (None, [])

    # Assert - Main Switch should have health_score < 100 (upgradable firmware)
    result = neo4j_session.run(
        """
        MATCH (d:UnifiDevice {id: 'AA:BB:CC:DD:EE:FF'})
        RETURN d.health_score as score, d.health_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["score"] == 80  # One issue (firmware_outdated)
    assert "firmware_outdated" in result[0]["issues"]
