from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.clients
import cartography.intel.unifi.dpi_apps
import cartography.intel.unifi.dpi_groups
import cartography.intel.unifi.sites
import cartography.intel.unifi.traffic_rules
import tests.data.unifi
from tests.integration.cartography.intel.unifi.test_devices import (
    _ensure_local_neo4j_has_test_devices,
)
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


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.traffic_rules,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_RULES,
)
async def test_unifi_traffic_rule_to_dpi_app_relationship(mock_get, neo4j_session):
    """
    Ensure that traffic rules with app_ids are linked to DPI apps via APPLIES_TO_APP.
    """
    neo4j_session.run(
        "MERGE (s:UnifiSite {id: 'default'}) SET s.lastupdated = $t",
        t=TEST_UPDATE_TAG,
    )
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Load DPI groups and apps via load functions directly
    cartography.intel.unifi.dpi_groups.load_dpi_groups(
        neo4j_session, tests.data.unifi.UNIFI_DPI_GROUPS, site_id, TEST_UPDATE_TAG
    )
    cartography.intel.unifi.dpi_apps.load_dpi_apps(
        neo4j_session, tests.data.unifi.UNIFI_DPI_APPS, site_id, TEST_UPDATE_TAG
    )
    await cartography.intel.unifi.traffic_rules.sync(
        neo4j_session, mock_controller, site_id, common_job_parameters
    )

    # tr_001 has app_ids: ["dpi_app_001"]
    expected_rels = {
        ("tr_001", "dpi_app_001"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiTrafficRule",
            "id",
            "UnifiDPIApp",
            "id",
            "APPLIES_TO_APP",
            rel_direction_right=True,
        )
        == expected_rels
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.traffic_rules,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_RULES,
)
async def test_unifi_traffic_rule_to_client_relationship(mock_get, neo4j_session):
    """
    Ensure that traffic rules with target_client_macs are linked to clients via APPLIES_TO_CLIENT.
    """
    neo4j_session.run(
        "MERGE (s:UnifiSite {id: 'default'}) SET s.lastupdated = $t",
        t=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_devices(neo4j_session)
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Load clients first
    cartography.intel.unifi.clients.load_clients(
        neo4j_session, tests.data.unifi.UNIFI_CLIENTS, site_id, TEST_UPDATE_TAG
    )
    await cartography.intel.unifi.traffic_rules.sync(
        neo4j_session, mock_controller, site_id, common_job_parameters
    )

    # tr_001 targets client 11:22:33:44:55:66
    expected_rels = {
        ("tr_001", "11:22:33:44:55:66"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiTrafficRule",
            "id",
            "UnifiClient",
            "id",
            "APPLIES_TO_CLIENT",
            rel_direction_right=True,
        )
        == expected_rels
    )
