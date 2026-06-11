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
async def test_firmware_compliance_analysis(mock_devices, neo4j_session):
    """
    Test that firmware compliance analysis correctly marks devices as compliant/non-compliant.
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
        "unifi_firmware_compliance.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Check that upgradable device (Main Switch) is non-compliant
    result = neo4j_session.run(
        """
        MATCH (d:UnifiDevice {id: 'AA:BB:CC:DD:EE:FF'})
        RETURN d.firmware_compliant as compliant, d.firmware_version_current as current, d.firmware_version_latest as latest
        """
    ).data()

    assert len(result) == 1
    assert result[0]["compliant"] is False
    assert result[0]["current"] == "6.5.28.14301"
    assert result[0]["latest"] == "6.5.29.14302"

    # Assert - Check that non-upgradable device (Office AP) is compliant
    result = neo4j_session.run(
        """
        MATCH (d:UnifiDevice {id: '00:11:22:33:44:55'})
        RETURN d.firmware_compliant as compliant, d.firmware_version_current as current, d.firmware_version_latest as latest
        """
    ).data()

    assert len(result) == 1
    assert result[0]["compliant"] is True
    assert result[0]["current"] == "6.5.28.14301"
    assert result[0]["latest"] == "6.5.28.14301"
