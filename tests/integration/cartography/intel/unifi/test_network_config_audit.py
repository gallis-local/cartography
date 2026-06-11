import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import cartography.intel.unifi.network_configs
import cartography.intel.unifi.firewall_zones
import cartography.intel.unifi.sites
import tests.data.unifi

# Add network config test data
UNIFI_NETWORK_CONFIGS = [
    {
        "id": "config_001",
        "name": "Guest Network Config",
        "enabled": True,
        "target_type": "network",
        "targets": ["network_guest"],
        "secure_enabled": True,
        "secure_firewall_rules": ["rule_001"],
        "secure_group_ids": ["fw_zone_002"],
        "qos_enabled": True,
        "qos_bandwidth_limit": 10000,
        "qos_dscp": 46,
        "route_enabled": False,
        "route_nexthop": None,
        "route_network": None,
        "site_id": "default",
    },
    {
        "id": "config_002",
        "name": "Disabled Config",
        "enabled": False,
        "target_type": "network",
        "targets": [],
        "secure_enabled": True,
        "secure_firewall_rules": None,
        "secure_group_ids": [],
        "qos_enabled": True,
        "qos_bandwidth_limit": None,
        "qos_dscp": None,
        "route_enabled": True,
        "route_nexthop": None,
        "route_network": None,
        "site_id": "default",
    },
]

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.network_configs,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_NETWORK_CONFIGS,
)
@patch.object(
    cartography.intel.unifi.firewall_zones,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_FIREWALL_ZONES,
)
async def test_network_config_audit(mock_fw_zones, mock_configs, neo4j_session):
    """
    Test that network configuration audit correctly scores configs.
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
    cartography.intel.unifi.firewall_zones.load_firewall_zones(
        neo4j_session, tests.data.unifi.UNIFI_FIREWALL_ZONES, "default", TEST_UPDATE_TAG
    )

    # Act - sync network configs
    await cartography.intel.unifi.network_configs.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Run analysis job directly
    from cartography.util import run_analysis_job

    run_analysis_job(
        "unifi_network_config_audit.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Config 001 should be compliant (score 100)
    result = neo4j_session.run(
        """
        MATCH (c:UnifiNetworkConfig {id: 'config_001'})
        RETURN c.audit_score as score, c.audit_tier as tier, c.audit_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["score"] == 100
    assert result[0]["tier"] == "compliant"

    # Assert - Config 002 should have multiple issues (disabled, no targets, secure no firewall, qos no limit, route incomplete)
    result = neo4j_session.run(
        """
        MATCH (c:UnifiNetworkConfig {id: 'config_002'})
        RETURN c.audit_score as score, c.audit_tier as tier, c.audit_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["score"] == 20  # 5 issues -> score 20
    assert result[0]["tier"] == "non_compliant"
    issues = result[0]["issues"]
    assert "disabled_config" in issues
    assert "no_targets" in issues
    assert "secure_no_firewall_rules" in issues
    assert "qos_no_bandwidth_limit" in issues
    assert "route_incomplete" in issues
