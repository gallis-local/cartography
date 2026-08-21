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
    common_job_parameters = {"UPDATE_TAG": 123456789, "host": "unifi-west.example.com"}
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
    common_job_parameters = {"UPDATE_TAG": 123456789, "host": "unifi-west.example.com"}
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
    common_job_parameters = {"UPDATE_TAG": 987654321, "host": "unifi-west.example.com"}
    await cartography.intel.unifi.sites.sync(neo4j_session, None, common_job_parameters)

    # Verify site was cleaned up
    result = neo4j_session.run(
        """
        MATCH (s:UnifiSite{id: 'default'})
        RETURN count(s) AS count
        """
    )
    assert result.single()["count"] == 0


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.sites,
    "get",
    new_callable=AsyncMock,
)
async def test_cleanup_unifi_sites_scoped_to_host(mock_get, neo4j_session):
    """
    Regression test: syncing one UniFi controller must not delete another
    controller's UnifiSite node. Before this was scoped by `host`, the
    cleanup query was global (`MATCH (s:UnifiSite) WHERE s.lastupdated <>
    $UPDATE_TAG DETACH DELETE s`), so every cronjob run for one controller
    would DETACH DELETE every other controller's site node, stranding its
    children (clients, port forwards, etc.) with a dangling site_id.
    """
    # Sync west controller's site
    mock_get.return_value = tests.data.unifi.UNIFI_SITES
    west_params = {"UPDATE_TAG": 111, "host": "unifi-west.example.com"}
    await cartography.intel.unifi.sites.sync(neo4j_session, None, west_params)

    # Sync east controller's site (same site id "default", different host,
    # later UPDATE_TAG - simulating the two cronjobs running independently)
    east_params = {"UPDATE_TAG": 222, "host": "unifi-east.example.com"}
    await cartography.intel.unifi.sites.sync(neo4j_session, None, east_params)

    # Both controllers' site nodes must survive - east's sync must not have
    # deleted west's site node just because it wasn't touched by UPDATE_TAG 222.
    result = neo4j_session.run(
        """
        MATCH (s:UnifiSite)
        RETURN s.host AS host, s.lastupdated AS lastupdated
        ORDER BY s.host
        """
    )
    records = result.data()
    assert len(records) == 2
    assert records[0] == {"host": "unifi-east.example.com", "lastupdated": 222}
    assert records[1] == {"host": "unifi-west.example.com", "lastupdated": 111}
