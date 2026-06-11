from unittest.mock import patch

import neo4j
import requests

import cartography.intel.fleetdm.hosts
import cartography.intel.fleetdm.tenant
import tests.data.fleetdm.hosts
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "https://fleet.example.com"


def _create_tenant(neo4j_session: neo4j.Session) -> None:
    cartography.intel.fleetdm.tenant.load_tenant(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.fleetdm.hosts,
    "get",
    return_value=tests.data.fleetdm.hosts.MOCK_HOSTS_RESPONSE,
)
def test_sync_fleetdm_hosts(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first (sub_resource_relationship uses OPTIONAL MATCH)
    _create_tenant(neo4j_session)

    # Act
    cartography.intel.fleetdm.hosts.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Tenant exists
    expected_nodes = {(TEST_TENANT_ID,)}
    assert (
        check_nodes(
            neo4j_session,
            "FleetDMTenant",
            ["id"],
        )
        == expected_nodes
    )

    # Assert Hosts exist
    expected_hosts = {
        ("1", "dev-macbook-pro.local"),
        ("2", "web-server-01.example.com"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "FleetDMHost",
            ["id", "hostname"],
        )
        == expected_hosts
    )

    # Assert Hosts are connected to Tenant via RESOURCE
    expected_rels = {
        ("1", TEST_TENANT_ID),
        ("2", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "FleetDMHost",
            "id",
            "FleetDMTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert host properties are correctly set
    nodes = check_nodes(
        neo4j_session,
        "FleetDMHost",
        ["id", "uuid", "platform", "os_version", "status", "cpu_brand", "memory"],
    )
    expected = {
        (
            "1",
            "550e8400-e29b-41d4-a716-446655440000",
            "darwin",
            "macOS 14.5",
            "online",
            "Apple M3 Pro",
            17179869184,
        ),
        (
            "2",
            "660e8400-e29b-41d4-a716-446655440001",
            "ubuntu",
            "Ubuntu 22.04.4 LTS",
            "offline",
            "Intel(R) Xeon(R) Platinum 8375C",
            32985348833,
        ),
    }
    assert nodes == expected


@patch.object(
    cartography.intel.fleetdm.hosts,
    "get",
    return_value=tests.data.fleetdm.hosts.MOCK_HOSTS_RESPONSE,
)
def test_fleetdm_hosts_cleanup(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first
    _create_tenant(neo4j_session)

    # Act - load with first update tag
    cartography.intel.fleetdm.hosts.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert - 2 hosts loaded
    initial = check_nodes(neo4j_session, "FleetDMHost", ["id"])
    assert initial is not None and len(initial) == 2

    # Act - sync with newer tag, empty data
    NEW_UPDATE_TAG = 999999999
    with patch.object(
        cartography.intel.fleetdm.hosts,
        "get",
        return_value=[],
    ):
        cartography.intel.fleetdm.hosts.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            NEW_UPDATE_TAG,
            {"UPDATE_TAG": NEW_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )

    # Assert - stale hosts cleaned up (0 remaining)
    remaining = check_nodes(neo4j_session, "FleetDMHost", ["id"])
    assert remaining is None or len(remaining) == 0
