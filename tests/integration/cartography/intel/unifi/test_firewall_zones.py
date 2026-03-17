from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.firewall_zones
import cartography.intel.unifi.sites
from cartography.intel.unifi.firewall_zones import sync
from tests.data.unifi import UNIFI_FIREWALL_ZONES
from tests.data.unifi import UNIFI_SITES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_SITE_ID = "default"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.firewall_zones,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_FIREWALL_ZONES,
)
async def test_sync_firewall_zones(mock_get, neo4j_session):
    """
    Test that firewall zones sync correctly
    """
    # Arrange
    controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "SITE_ID": TEST_SITE_ID}

    # Act
    await sync(
        neo4j_session, controller, TEST_SITE_ID, common_job_parameters
    )

    # Assert
    expected_nodes = {
        ("fw_zone_001", "LAN"),
        ("fw_zone_002", "WAN"),
    }
    assert (
        check_nodes(neo4j_session, "UnifiFirewallZone", ["id", "name"])
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.firewall_zones,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_FIREWALL_ZONES,
)
async def test_sync_firewall_zones_relationships(mock_get, neo4j_session):
    """
    Test that firewall zone relationships are created correctly
    """
    # Arrange
    # Create the UnifiSite node first
    neo4j_session.run(
        """
        MERGE (s:UnifiSite{id: $site_id})
        ON CREATE SET s.firstseen = timestamp()
        SET s.name = 'Default', s.lastupdated = $update_tag
        """,
        site_id=TEST_SITE_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "SITE_ID": TEST_SITE_ID}

    # Act
    await sync(
        neo4j_session, controller, TEST_SITE_ID, common_job_parameters
    )

    # Assert - Check RESOURCE relationships
    expected_rels = {
        ("fw_zone_001", TEST_SITE_ID),
        ("fw_zone_002", TEST_SITE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiFirewallZone",
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
    cartography.intel.unifi.firewall_zones,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_FIREWALL_ZONES,
)
async def test_sync_firewall_zones_cleanup(mock_get, neo4j_session):
    """
    Test that stale firewall zones are cleaned up
    """
    # Arrange
    # Load the UnifiSite using the actual load function
    cartography.intel.unifi.sites.load_sites(
        neo4j_session,
        UNIFI_SITES,
        TEST_UPDATE_TAG,
    )

    # Create a stale firewall zone using the load function
    stale_zone = [
        {
            "id": "stale_zone",
            "name": "Stale Zone",
            "attr_no_edit": False,
            "default_zone": False,
            "zone_key": "stale",
            "network_ids": [],
            "site_id": TEST_SITE_ID,
        }
    ]
    cartography.intel.unifi.firewall_zones.load_firewall_zones(
        neo4j_session,
        stale_zone,
        TEST_SITE_ID,
        TEST_UPDATE_TAG - 1,
    )

    controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "SITE_ID": TEST_SITE_ID}

    # Act
    await sync(
        neo4j_session, controller, TEST_SITE_ID, common_job_parameters
    )

    # Assert - Stale zone should be removed
    nodes = check_nodes(neo4j_session, "UnifiFirewallZone", ["id"])
    assert ("stale_zone",) not in nodes
    assert ("fw_zone_001",) in nodes
    assert ("fw_zone_002",) in nodes
