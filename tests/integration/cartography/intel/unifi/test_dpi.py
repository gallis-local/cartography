import pytest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.unifi.dpi_apps
import cartography.intel.unifi.dpi_groups
import tests.data.unifi
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.dpi_groups,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DPI_GROUPS,
)
async def test_load_unifi_dpi_groups(mock_get, neo4j_session):
    """
    Ensure that UniFi DPI groups actually get loaded.
    """
    # Arrange
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.dpi_groups.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check that DPI groups were loaded with correct properties
    expected_nodes = {
        ("dpi_group_001", "Restricted Apps", False),
        ("dpi_group_002", "Default", True),
    }
    assert (
        check_nodes(
            neo4j_session,
            "UnifiDPIGroup",
            ["id", "name", "attr_no_delete"],
        )
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.dpi_apps,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DPI_APPS,
)
async def test_load_unifi_dpi_apps(mock_get, neo4j_session):
    """
    Ensure that UniFi DPI apps actually get loaded.
    """
    # Arrange
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.dpi_apps.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check that DPI apps were loaded with correct properties
    expected_nodes = {
        ("dpi_app_001", True, True),
        ("dpi_app_002", False, True),
    }
    assert (
        check_nodes(
            neo4j_session,
            "UnifiDPIApp",
            ["id", "blocked", "enabled"],
        )
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.dpi_groups,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DPI_GROUPS,
)
@patch.object(
    cartography.intel.unifi.dpi_apps,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DPI_APPS,
)
async def test_unifi_dpi_app_to_group_relationship(mock_apps, mock_groups, neo4j_session):
    """
    Ensure that DPI apps are connected to DPI groups.
    """
    # Arrange - Load groups first
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Load groups first
    await cartography.intel.unifi.dpi_groups.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Act - Load apps
    await cartography.intel.unifi.dpi_apps.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check relationship exists
    expected_rels = {
        ("dpi_app_001", "dpi_group_001"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiDPIApp",
            "id",
            "UnifiDPIGroup",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
