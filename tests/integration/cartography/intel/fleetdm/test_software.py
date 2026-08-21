from unittest.mock import patch

import neo4j
import requests

import cartography.intel.fleetdm.software
import cartography.intel.fleetdm.tenant
import tests.data.fleetdm.software
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
    cartography.intel.fleetdm.software,
    "get",
    return_value=tests.data.fleetdm.software.MOCK_SOFTWARE_RESPONSE["software_titles"],
)
def test_sync_fleetdm_software(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first (sub_resource_relationship uses OPTIONAL MATCH)
    _create_tenant(neo4j_session)

    # Act
    cartography.intel.fleetdm.software.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Software titles exist
    expected_software = {
        ("100", "Slack", "apps"),
        ("101", "glibc", "rpm_packages"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "FleetDMSoftware",
            ["id", "name", "source"],
        )
        == expected_software
    )

    # Assert Software titles are connected to Tenant via RESOURCE
    expected_rels = {
        ("100", TEST_TENANT_ID),
        ("101", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "FleetDMSoftware",
            "id",
            "FleetDMTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.fleetdm.software,
    "get",
    return_value=tests.data.fleetdm.software.MOCK_SOFTWARE_RESPONSE["software_titles"],
)
def test_fleetdm_software_cleanup(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first
    _create_tenant(neo4j_session)

    # Act - load with first update tag
    cartography.intel.fleetdm.software.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert - 2 software titles loaded
    initial = check_nodes(neo4j_session, "FleetDMSoftware", ["id"])
    assert initial is not None and len(initial) == 2

    # Act - sync with newer tag, empty data
    NEW_UPDATE_TAG = 999999999
    with patch.object(
        cartography.intel.fleetdm.software,
        "get",
        return_value=[],
    ):
        cartography.intel.fleetdm.software.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            NEW_UPDATE_TAG,
            {"UPDATE_TAG": NEW_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )

    # Assert - stale software titles cleaned up (0 remaining)
    remaining = check_nodes(neo4j_session, "FleetDMSoftware", ["id"])
    assert remaining is None or len(remaining) == 0
