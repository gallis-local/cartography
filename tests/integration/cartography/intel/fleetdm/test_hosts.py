from unittest.mock import patch

import neo4j
import requests

import cartography.intel.fleetdm.hosts
import cartography.intel.fleetdm.labels
import cartography.intel.fleetdm.policies
import cartography.intel.fleetdm.tenant
import cartography.intel.fleetdm.versions
import tests.data.fleetdm.hosts
import tests.data.fleetdm.labels
import tests.data.fleetdm.policies
import tests.data.fleetdm.versions
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


def _create_related_entities(neo4j_session: neo4j.Session) -> None:
    """Load the FleetDMSoftwareVersion, FleetDMPolicy, and FleetDMLabel nodes
    that the host mock data's software/policies/labels arrays reference, so
    the host-to-{software,policy,label} relationships can be asserted."""
    session = requests.Session()
    with patch.object(
        cartography.intel.fleetdm.versions,
        "get",
        return_value=tests.data.fleetdm.versions.MOCK_VERSIONS_RESPONSE,
    ):
        cartography.intel.fleetdm.versions.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )
    with patch.object(
        cartography.intel.fleetdm.policies,
        "get",
        return_value=tests.data.fleetdm.policies.MOCK_POLICIES_RESPONSE["policies"],
    ):
        cartography.intel.fleetdm.policies.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )
    with patch.object(
        cartography.intel.fleetdm.labels,
        "get",
        return_value=tests.data.fleetdm.labels.MOCK_LABELS_RESPONSE["labels"],
    ):
        cartography.intel.fleetdm.labels.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
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
    _create_related_entities(neo4j_session)

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

    # Assert new host detail properties (team_id, mdm, geolocation) are captured
    detail_nodes = check_nodes(
        neo4j_session,
        "FleetDMHost",
        [
            "id",
            "team_id",
            "mdm_enrollment_status",
            "mdm_name",
            "mdm_server_url",
            "geolocation_country_iso",
            "geolocation_city_name",
        ],
    )
    assert detail_nodes == {
        (
            "1",
            None,
            "Enrolled",
            "Fleet",
            "https://fleet.example.com/mdm/apple/mdm",
            "US",
            "San Francisco",
        ),
        (
            "2",
            "1",
            "Unenrolled",
            "",
            None,
            "US",
            "Ashburn",
        ),
    }

    # Assert host 1 is connected to its installed software version via HAS_SOFTWARE
    assert check_rels(
        neo4j_session,
        "FleetDMHost",
        "id",
        "FleetDMSoftwareVersion",
        "id",
        "HAS_SOFTWARE",
        rel_direction_right=True,
    ) == {("1", "1")}

    # Assert host 1 is connected to its labels via MEMBER_OF_LABEL
    assert check_rels(
        neo4j_session,
        "FleetDMHost",
        "id",
        "FleetDMLabel",
        "id",
        "MEMBER_OF_LABEL",
        rel_direction_right=True,
    ) == {("1", "1"), ("1", "2")}

    # Assert host 1's per-policy check results are connected via CHECKS, with
    # the pass/fail response captured as a relationship property
    result = neo4j_session.run(
        """
        MATCH (h:FleetDMHost {id: '1'})-[r:CHECKS]->(p:FleetDMPolicy)
        RETURN p.id AS policy_id, r.response AS response ORDER BY policy_id
        """
    )
    checks = {(record["policy_id"], record["response"]) for record in result}
    assert checks == {("1", "pass"), ("2", "fail")}


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
