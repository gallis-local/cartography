import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import cartography.intel.unifi.speedtests
import cartography.intel.unifi.devices
import cartography.intel.unifi.sites
import tests.data.unifi

# Add speedtest test data
UNIFI_SPEEDTESTS = [
    {
        "id": "wan1",
        "interface_name": "wan1",
        "download": 100.5,
        "upload": 20.2,
        "ping": 15,
        "timestamp": 1638342818,
        "gateway_mac": "AA:BB:CC:DD:EE:FF",
        "site_id": "default",
    },
    {
        "id": "wan2",
        "interface_name": "wan2",
        "download": 10.0,
        "upload": 2.0,
        "ping": 150,
        "timestamp": 1638342818,
        "gateway_mac": "AA:BB:CC:DD:EE:FF",
        "site_id": "default",
    },
]

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.speedtests,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_SPEEDTESTS,
)
@patch.object(
    cartography.intel.unifi.devices,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DEVICES,
)
async def test_wan_performance_analysis(mock_devices, mock_speedtests, neo4j_session):
    """
    Test that WAN performance analysis correctly scores speedtest results.
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

    # Act - sync speedtests
    await cartography.intel.unifi.speedtests.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Run analysis job directly
    from cartography.util import run_analysis_job

    run_analysis_job(
        "unifi_wan_performance.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert - wan1 (good performance) should score 100
    result = neo4j_session.run(
        """
        MATCH (s:UnifiSpeedtest {id: 'wan1'})
        RETURN s.performance_score as score, s.performance_tier as tier, s.performance_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["score"] == 100
    assert result[0]["tier"] == "excellent"
    assert result[0]["issues"] == []

    # Assert - wan2 (poor performance: low download, low upload, high ping) should score 20
    result = neo4j_session.run(
        """
        MATCH (s:UnifiSpeedtest {id: 'wan2'})
        RETURN s.performance_score as score, s.performance_tier as tier, s.performance_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["score"] == 20  # 3 issues
    assert result[0]["tier"] == "poor"
    issues = result[0]["issues"]
    assert "low_download" in issues
    assert "low_upload" in issues
    assert "high_latency" in issues
