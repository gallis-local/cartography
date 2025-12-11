from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.sites
import tests.data.unifi


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.sites,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_SITES,
)
async def test_load_unifi_sites(mock_get, neo4j_session):
    """
    Test that we can load UniFi sites into Neo4j.
    """
    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.sites.sync(neo4j_session, None, common_job_parameters)

    # Verify the site was loaded
    result = neo4j_session.run(
        """
        MATCH (s:UnifiSite{id: 'default'})
        RETURN s.name AS name, s.desc AS desc, s.role AS role
        """
    )
    record = result.single()
    assert record is not None
    assert record["name"] == "Default"
    assert record["desc"] == "Default Site"
    assert record["role"] == "admin"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.sites,
    "get",
    new_callable=AsyncMock,
    return_value=tests.data.unifi.UNIFI_SITES,
)
async def test_cleanup_unifi_sites(mock_get, neo4j_session):
    """
    Test that stale UniFi sites are cleaned up.
    """
    # First sync
    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.sites.sync(neo4j_session, None, common_job_parameters)

    # Verify site exists
    result = neo4j_session.run(
        """
        MATCH (s:UnifiSite{id: 'default'})
        RETURN count(s) AS count
        """
    )
    assert result.single()["count"] == 1

    # Second sync with a new update tag (simulating site removal)
    mock_get.return_value = []
    common_job_parameters = {"UPDATE_TAG": 987654321}
    await cartography.intel.unifi.sites.sync(neo4j_session, None, common_job_parameters)

    # Verify site was cleaned up
    result = neo4j_session.run(
        """
        MATCH (s:UnifiSite{id: 'default'})
        RETURN count(s) AS count
        """
    )
    assert result.single()["count"] == 0
