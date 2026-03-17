from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.system_info
from cartography.intel.unifi.system_info import sync
from tests.data.unifi import UNIFI_SYSTEM_INFO
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_SITE_ID = "default"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.system_info,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_SYSTEM_INFO,
)
async def test_sync_system_info(mock_get, neo4j_session):
    """
    Test that system information syncs correctly
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
        ("controller_001", "unifi-controller"),
    }
    assert (
        check_nodes(neo4j_session, "UnifiSystemInfo", ["id", "hostname"])
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.system_info,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_SYSTEM_INFO,
)
async def test_sync_system_info_relationships(mock_get, neo4j_session):
    """
    Test that system information relationships are created correctly
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
        ("controller_001", TEST_SITE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiSystemInfo",
            "id",
            "UnifiSite",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
