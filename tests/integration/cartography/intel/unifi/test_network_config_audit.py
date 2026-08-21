import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import cartography.intel.unifi.network_configs
import cartography.intel.unifi.sites
import tests.data.unifi

# Add network config test data, shaped like the real /rest/networkconf response.
UNIFI_NETWORK_CONFIGS = [
    {
        "id": "config_001",
        "name": "Corporate LAN",
        "enabled": True,
        "purpose": "corporate",
        "networkgroup": "LAN",
        "domain_name": "lan",
        "vlan_enabled": True,
        "vlan": 10,
        "ip_subnet": "10.0.10.1/24",
        "is_guest": False,
        "is_nat": True,
        "attr_no_delete": True,
        "dhcpd_enabled": True,
        "dhcpd_start": "10.0.10.100",
        "dhcpd_stop": "10.0.10.200",
        "dhcpd_leasetime": 86400,
        "dhcpd_dns_enabled": True,
        "dhcpd_dns_1": "10.0.10.1",
        "site_id": "default",
    },
    {
        "id": "config_002",
        "name": "Guest Network",
        "enabled": False,
        "purpose": "guest",
        "networkgroup": "WAN",
        "domain_name": None,
        "vlan_enabled": True,
        "vlan": None,
        "ip_subnet": None,
        "is_guest": True,
        "is_nat": False,
        "attr_no_delete": False,
        "dhcpd_enabled": False,
        "dhcpd_start": None,
        "dhcpd_stop": None,
        "dhcpd_leasetime": None,
        "dhcpd_dns_enabled": True,
        "dhcpd_dns_1": None,
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
async def test_network_config_audit(mock_configs, neo4j_session):
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

    # Assert - Config 001 (fully configured corporate VLAN) should be compliant
    result = neo4j_session.run(
        """
        MATCH (c:UnifiNetworkConfig {id: 'config_001'})
        RETURN c.audit_score as score, c.audit_tier as tier, c.audit_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["score"] == 100
    assert result[0]["tier"] == "compliant"

    # Assert - Config 002 (disabled guest network, VLAN enabled but no VLAN id,
    # no DHCP, and not NAT'd) should have multiple issues
    result = neo4j_session.run(
        """
        MATCH (c:UnifiNetworkConfig {id: 'config_002'})
        RETURN c.audit_score as score, c.audit_tier as tier, c.audit_issues as issues
        """
    ).data()

    assert len(result) == 1
    assert result[0]["score"] == 20  # 4 issues -> score 20
    assert result[0]["tier"] == "non_compliant"
    issues = result[0]["issues"]
    assert "disabled_config" in issues
    assert "vlan_enabled_without_vlan_id" in issues
    assert "guest_network_without_dhcp" in issues
    assert "guest_network_not_natted" in issues
