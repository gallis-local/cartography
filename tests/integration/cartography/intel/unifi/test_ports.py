from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.devices
import cartography.intel.unifi.ports
import cartography.intel.unifi.sites
import tests.data.unifi


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.ports,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_PORTS, "default"),
)
async def test_load_unifi_ports(mock_get, neo4j_session):
    """
    Test that we can load UniFi ports into Neo4j.
    """
    # First load the site
    neo4j_session.run(
        """
        MERGE (s:UnifiSite{id: 'default'})
        SET s.name = 'Default', s.lastupdated = 123456789
        """
    )

    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.ports.sync(neo4j_session, None, common_job_parameters)

    # Verify the ports were loaded
    result = neo4j_session.run(
        """
        MATCH (p:UnifiPort)
        RETURN p.id AS id, p.port_idx AS port_idx, p.name AS name
        ORDER BY p.port_idx
        """
    )
    records = list(result)
    assert len(records) == 2

    # Check Port 1
    assert records[0]["id"] == "AA:BB:CC:DD:EE:FF:1"
    assert records[0]["port_idx"] == 1
    assert records[0]["name"] == "Port 1"

    # Check Port 2
    assert records[1]["id"] == "AA:BB:CC:DD:EE:FF:2"
    assert records[1]["port_idx"] == 2
    assert records[1]["name"] == "Port 2"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.ports,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_PORTS, "default"),
)
async def test_port_poe_properties(mock_get, neo4j_session):
    """
    Test that PoE port properties are loaded correctly.
    """
    # First load the site
    neo4j_session.run(
        """
        MERGE (s:UnifiSite{id: 'default'})
        SET s.name = 'Default', s.lastupdated = 123456789
        """
    )

    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.ports.sync(neo4j_session, None, common_job_parameters)

    # Check Port 1 PoE properties
    result = neo4j_session.run(
        """
        MATCH (p:UnifiPort{id: 'AA:BB:CC:DD:EE:FF:1'})
        RETURN p.port_poe AS port_poe, p.poe_enable AS poe_enable,
               p.poe_mode AS poe_mode, p.poe_voltage AS poe_voltage
        """
    )
    record = result.single()
    assert record["port_poe"] is True
    assert record["poe_enable"] is True
    assert record["poe_mode"] == "auto"
    assert record["poe_voltage"] == 48.0

    # Check Port 2 (no PoE enabled)
    result = neo4j_session.run(
        """
        MATCH (p:UnifiPort{id: 'AA:BB:CC:DD:EE:FF:2'})
        RETURN p.poe_enable AS poe_enable
        """
    )
    record = result.single()
    assert record["poe_enable"] is False


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.ports,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_PORTS, "default"),
)
async def test_port_connectivity_properties(mock_get, neo4j_session):
    """
    Test that port connectivity properties are loaded correctly.
    """
    # First load the site
    neo4j_session.run(
        """
        MERGE (s:UnifiSite{id: 'default'})
        SET s.name = 'Default', s.lastupdated = 123456789
        """
    )

    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.ports.sync(neo4j_session, None, common_job_parameters)

    # Check Port 1 connectivity (up and running)
    result = neo4j_session.run(
        """
        MATCH (p:UnifiPort{id: 'AA:BB:CC:DD:EE:FF:1'})
        RETURN p.up AS up, p.speed AS speed, p.full_duplex AS full_duplex
        """
    )
    record = result.single()
    assert record["up"] is True
    assert record["speed"] == 1000
    assert record["full_duplex"] is True

    # Check Port 2 connectivity (down)
    result = neo4j_session.run(
        """
        MATCH (p:UnifiPort{id: 'AA:BB:CC:DD:EE:FF:2'})
        RETURN p.up AS up, p.speed AS speed
        """
    )
    record = result.single()
    assert record["up"] is False
    assert record["speed"] == 0


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.ports,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_PORTS, "default"),
)
async def test_port_to_device_relationship(mock_get, neo4j_session):
    """
    Test that ports are correctly linked to their device.
    """
    # First load the site and devices using actual load functions
    cartography.intel.unifi.sites.load_sites(
        neo4j_session,
        tests.data.unifi.UNIFI_SITES,
        123456789,
    )
    cartography.intel.unifi.devices.load_devices(
        neo4j_session,
        tests.data.unifi.UNIFI_DEVICES,
        "default",
        123456789,
    )

    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.ports.sync(neo4j_session, None, common_job_parameters)

    # Verify the relationship
    result = neo4j_session.run(
        """
        MATCH (d:UnifiDevice{id: 'AA:BB:CC:DD:EE:FF'})-[:HAS_PORT]->(p:UnifiPort)
        RETURN count(p) AS count
        """
    )
    assert result.single()["count"] == 2


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.ports,
    "get",
    new_callable=AsyncMock,
    return_value=(tests.data.unifi.UNIFI_PORTS, "default"),
)
async def test_cleanup_unifi_ports(mock_get, neo4j_session):
    """
    Test that stale UniFi ports are cleaned up.
    """
    # First load the site
    neo4j_session.run(
        """
        MERGE (s:UnifiSite{id: 'default'})
        SET s.name = 'Default', s.lastupdated = 123456789
        """
    )

    # First sync
    common_job_parameters = {"UPDATE_TAG": 123456789}
    await cartography.intel.unifi.ports.sync(neo4j_session, None, common_job_parameters)

    # Verify ports exist
    result = neo4j_session.run(
        """
        MATCH (p:UnifiPort)
        RETURN count(p) AS count
        """
    )
    assert result.single()["count"] == 2

    # Second sync with a new update tag (simulating port removal)
    mock_get.return_value = ([], "default")
    common_job_parameters = {"UPDATE_TAG": 987654321}
    await cartography.intel.unifi.ports.sync(neo4j_session, None, common_job_parameters)

    # Verify ports were cleaned up
    result = neo4j_session.run(
        """
        MATCH (p:UnifiPort)
        RETURN count(p) AS count
        """
    )
    assert result.single()["count"] == 0
