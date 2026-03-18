from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.dpi_apps
import cartography.intel.unifi.dpi_groups
import cartography.intel.unifi.sites
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
        "site_id": site_id,
    }

    # Act
    await cartography.intel.unifi.dpi_groups.sync(
        neo4j_session,
        mock_controller,
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
        "site_id": site_id,
    }

    # Act
    await cartography.intel.unifi.dpi_apps.sync(
        neo4j_session,
        mock_controller,
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
    cartography.intel.unifi.dpi_apps,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_DPI_APPS,
)
async def test_unifi_dpi_app_to_site_relationship(mock_apps, neo4j_session):
    """
    Ensure that DPI apps are connected to their site via the RESOURCE relationship.
    MEMBER_OF (app→group) was removed; the canonical direction is
    Group-[:CONTAINS_APP]->App, tested in test_unifi_dpi_group_contains_app_relationship.
    """
    # Site must exist before loading apps so the RESOURCE relationship can be created
    cartography.intel.unifi.sites.load_sites(
        neo4j_session, tests.data.unifi.UNIFI_SITES, TEST_UPDATE_TAG
    )
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "site_id": site_id}

    await cartography.intel.unifi.dpi_apps.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # Both apps belong to the default site
    expected_rels = {
        ("dpi_app_001", "default"),
        ("dpi_app_002", "default"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiDPIApp",
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
async def test_unifi_dpi_group_contains_app_relationship(
    mock_apps, mock_groups, neo4j_session
):
    """
    Ensure that DPI groups are linked to their member apps via CONTAINS_APP.
    """
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "site_id": site_id}

    # Load apps first so group→app relationship can be resolved
    await cartography.intel.unifi.dpi_apps.sync(
        neo4j_session, mock_controller, common_job_parameters
    )
    await cartography.intel.unifi.dpi_groups.sync(
        neo4j_session, mock_controller, common_job_parameters
    )

    # dpi_group_001 contains dpi_app_001
    # dpi_group_002 contains dpi_app_001 and dpi_app_002
    expected_rels = {
        ("dpi_group_001", "dpi_app_001"),
        ("dpi_group_002", "dpi_app_001"),
        ("dpi_group_002", "dpi_app_002"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiDPIGroup",
            "id",
            "UnifiDPIApp",
            "id",
            "CONTAINS_APP",
            rel_direction_right=True,
        )
        == expected_rels
    )
