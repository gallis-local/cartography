from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.admins
import cartography.intel.unifi.sites
from tests.data.unifi import UNIFI_ADMINS
from tests.data.unifi import UNIFI_SITES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_SITE_ID = "default"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.admins,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_ADMINS,
)
async def test_load_unifi_admins(mock_get, neo4j_session):
    """Test that UniFi admins are loaded correctly."""
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.admins.sync(
        neo4j_session, MagicMock(), TEST_SITE_ID, common_job_parameters
    )

    expected_nodes = {
        ("admin_001", "alice", "alice@example.com", "admin"),
        ("admin_002", "bob", "bob@example.com", "readonly"),
    }
    assert (
        check_nodes(neo4j_session, "UnifiAdmin", ["id", "name", "email", "role"])
        == expected_nodes
    )


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.admins,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_ADMINS,
)
async def test_unifi_admin_has_useraccount_label(mock_get, neo4j_session):
    """Test that UnifiAdmin nodes receive the UserAccount semantic label."""
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.admins.sync(
        neo4j_session, MagicMock(), TEST_SITE_ID, common_job_parameters
    )

    result = neo4j_session.run(
        "MATCH (a:UnifiAdmin:UserAccount{id: $id}) RETURN a.id AS id",
        id="admin_001",
    ).single()
    assert result is not None
    assert result["id"] == "admin_001"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.admins,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_ADMINS,
)
async def test_unifi_admin_to_site_relationship(mock_get, neo4j_session):
    """Test that UnifiAdmin nodes are linked to their UnifiSite via RESOURCE."""
    cartography.intel.unifi.sites.load_sites(
        neo4j_session, UNIFI_SITES, TEST_UPDATE_TAG
    )
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    await cartography.intel.unifi.admins.sync(
        neo4j_session, MagicMock(), TEST_SITE_ID, common_job_parameters
    )

    expected_rels = {
        ("admin_001", TEST_SITE_ID),
        ("admin_002", TEST_SITE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiAdmin",
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
    cartography.intel.unifi.admins,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_ADMINS,
)
async def test_cleanup_unifi_admins(mock_get, neo4j_session):
    """Test that stale UniFi admins are cleaned up."""
    cartography.intel.unifi.sites.load_sites(
        neo4j_session, UNIFI_SITES, TEST_UPDATE_TAG
    )

    stale_admin = [
        {
            "id": "stale_admin",
            "name": "stale",
            "email": "stale@example.com",
            "role": "admin",
            "is_super_admin": False,
            "last_site_name": "Default",
        }
    ]
    cartography.intel.unifi.admins.load_admins(
        neo4j_session,
        stale_admin,
        TEST_SITE_ID,
        TEST_UPDATE_TAG - 1,
    )

    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    await cartography.intel.unifi.admins.sync(
        neo4j_session, MagicMock(), TEST_SITE_ID, common_job_parameters
    )

    nodes = check_nodes(neo4j_session, "UnifiAdmin", ["id"])
    assert ("stale_admin",) not in nodes
    assert ("admin_001",) in nodes
    assert ("admin_002",) in nodes
