import pytest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.unifi.firewall_policies
import tests.data.unifi
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.firewall_policies,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_FIREWALL_POLICIES,
)
async def test_load_unifi_firewall_policies(mock_get, neo4j_session):
    """
    Ensure that UniFi firewall policies actually get loaded.
    """
    # Arrange
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.firewall_policies.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check that firewall policies were loaded with correct properties
    expected_nodes = {
        ("fw_policy_001", "Allow LAN to WAN", "ALLOW"),
        ("fw_policy_002", "Block Guest to LAN", "DENY"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "UnifiFirewallPolicy",
            ["id", "name", "action"],
        )
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.firewall_policies,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_FIREWALL_POLICIES,
)
async def test_unifi_firewall_policy_to_site_relationship(mock_get, neo4j_session):
    """
    Ensure that firewall policies are connected to sites.
    """
    # Arrange - Load site first
    neo4j_session.run(
        """
        MERGE (s:UnifiSite {id: $site_id})
        SET s.lastupdated = $update_tag
        """,
        site_id="default",
        update_tag=TEST_UPDATE_TAG,
    )

    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.firewall_policies.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check relationship exists
    expected_rels = {
        ("fw_policy_001", "default"),
        ("fw_policy_002", "default"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiFirewallPolicy",
            "id",
            "UnifiSite",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.firewall_policies,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_FIREWALL_POLICIES,
)
async def test_unifi_firewall_policy_properties(mock_get, neo4j_session):
    """
    Ensure that firewall policy properties are correctly set.
    """
    # Arrange
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.firewall_policies.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check detailed properties of firewall policies
    result = neo4j_session.run(
        """
        MATCH (fp:UnifiFirewallPolicy {id: $policy_id})
        RETURN fp.enabled as enabled, fp.logging as logging, fp.predefined as predefined
        """,
        policy_id="fw_policy_002",
    )
    record = result.single()
    assert record is not None
    assert record["enabled"] is True
    assert record["logging"] is True
    assert record["predefined"] is False
