from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.clients
import cartography.intel.unifi.sites
import cartography.intel.unifi.traffic_routes
import tests.data.unifi
from tests.integration.cartography.intel.unifi.test_devices import (
    _ensure_local_neo4j_has_test_devices,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.traffic_routes,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_ROUTES,
)
async def test_load_unifi_traffic_routes(mock_get, neo4j_session):
    """
    Ensure that UniFi traffic routes actually get loaded.
    """
    # Arrange
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.traffic_routes.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check that traffic routes were loaded with correct properties
    expected_nodes = {
        ("route_001", "VPN Route", "IP"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "UnifiTrafficRoute",
            ["id", "description", "matching_target"],
        )
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.traffic_routes,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_ROUTES,
)
async def test_unifi_traffic_route_to_site_relationship(mock_get, neo4j_session):
    """
    Ensure that traffic routes are connected to sites.
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
    await cartography.intel.unifi.traffic_routes.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check relationship exists
    expected_rels = {
        ("route_001", "default"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiTrafficRoute",
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
    cartography.intel.unifi.traffic_routes,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_ROUTES,
)
async def test_unifi_traffic_route_properties(mock_get, neo4j_session):
    """
    Ensure that traffic route properties are correctly set.
    """
    # Arrange
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.traffic_routes.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check detailed properties
    result = neo4j_session.run(
        """
        MATCH (r:UnifiTrafficRoute {id: $route_id})
        RETURN r.enabled AS enabled, r.next_hop AS next_hop, r.network_id AS network_id
        """,
        route_id="route_001",
    )
    record = result.single()
    assert record is not None
    assert record["enabled"] is True
    assert record["next_hop"] == "192.168.1.1"
    assert record["network_id"] == "network_001"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.traffic_routes,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_ROUTES,
)
async def test_unifi_traffic_route_cleanup(mock_get, neo4j_session):
    """
    Ensure that stale UniFi traffic routes are cleaned up after sync.
    """
    # Arrange - Load a site and a stale route connected to it with old update tag
    neo4j_session.run(
        """
        MERGE (s:UnifiSite {id: $site_id})
        SET s.lastupdated = $update_tag
        MERGE (r:UnifiTrafficRoute {id: 'stale_route'})
        SET r.lastupdated = $old_tag
        MERGE (r)<-[:RESOURCE]-(s)
        """,
        site_id="default",
        update_tag=TEST_UPDATE_TAG,
        old_tag=TEST_UPDATE_TAG - 1,
    )

    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.traffic_routes.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Stale route should be gone
    result = neo4j_session.run(
        """
        MATCH (r:UnifiTrafficRoute {id: 'stale_route'})
        RETURN count(r) AS count
        """
    )
    assert result.single()["count"] == 0


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.traffic_routes,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_TRAFFIC_ROUTES,
)
async def test_unifi_traffic_route_to_client_relationship(mock_get, neo4j_session):
    """
    Ensure that traffic routes with target_client_macs are linked to clients via APPLIES_TO_CLIENT.
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
    await cartography.intel.unifi.traffic_routes.sync(
        neo4j_session, mock_controller, site_id, common_job_parameters
    )

    # route_001 targets client DD:EE:FF:00:11:22 (wired workstation)
    expected_rels = {
        ("route_001", "DD:EE:FF:00:11:22"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiTrafficRoute",
            "id",
            "UnifiClient",
            "id",
            "APPLIES_TO_CLIENT",
            rel_direction_right=True,
        )
        == expected_rels
    )
