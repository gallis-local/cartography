import pytest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.unifi.port_forwards
import tests.data.unifi
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.port_forwards,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_PORT_FORWARDS,
)
async def test_load_unifi_port_forwards(mock_get, neo4j_session):
    """
    Ensure that UniFi port forwards actually get loaded.
    """
    # Arrange
    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.port_forwards.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check that port forwards were loaded with correct properties
    expected_nodes = {
        ("pf_001", "Web Server", True),
        ("pf_002", "SSH Server", False),
    }
    assert (
        check_nodes(
            neo4j_session,
            "UnifiPortForward",
            ["id", "name", "enabled"],
        )
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.port_forwards,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_PORT_FORWARDS,
)
async def test_unifi_port_forward_to_site_relationship(mock_get, neo4j_session):
    """
    Ensure that port forwards are connected to sites.
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
    await cartography.intel.unifi.port_forwards.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Check relationship exists
    expected_rels = {
        ("pf_001", "default"),
        ("pf_002", "default"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiPortForward",
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
    cartography.intel.unifi.port_forwards,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_PORT_FORWARDS,
)
async def test_unifi_port_forward_cleanup(mock_get, neo4j_session):
    """
    Ensure that stale port forwards are cleaned up.
    """
    # Arrange - Create an old port forward
    neo4j_session.run(
        """
        MERGE (pf:UnifiPortForward {id: $pf_id})
        SET pf.lastupdated = $old_update_tag
        """,
        pf_id="old_pf",
        old_update_tag=TEST_UPDATE_TAG - 1,
    )

    mock_controller = MagicMock()
    site_id = "default"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    await cartography.intel.unifi.port_forwards.sync(
        neo4j_session,
        mock_controller,
        site_id,
        common_job_parameters,
    )

    # Assert - Old port forward should be cleaned up
    expected_nodes = {
        ("pf_001", "Web Server"),
        ("pf_002", "SSH Server"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "UnifiPortForward",
            ["id", "name"],
        )
        == expected_nodes
    )
