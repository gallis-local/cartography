from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.traffic_rules
import tests.data.unifi
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.traffic_rules,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_RULES,
)
async def test_load_unifi_traffic_rules(mock_get, neo4j_session):
    """
    Ensure that UniFi traffic rules actually get loaded.
    """
    # Arrange
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.traffic_rules.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check that traffic rules were loaded with correct properties
    expected_nodes = {
        ("tr_001", "Block Social Media", "BLOCK"),
        ("tr_002", "Limit Guest Bandwidth", "ALLOW"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "UnifiTrafficRule",
            ["id", "description", "action"],
        )
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.traffic_rules,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_RULES,
)
async def test_unifi_traffic_rule_to_site_relationship(mock_get, neo4j_session):
    """
    Ensure that traffic rules are connected to sites.
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
    await cartography.intel.unifi.traffic_rules.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check relationship exists
    expected_rels = {
        ("tr_001", "default"),
        ("tr_002", "default"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiTrafficRule",
            "id",
            "UnifiSite",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
