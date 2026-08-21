from unittest.mock import patch

import neo4j
import requests

import cartography.intel.fleetdm.fleets
import cartography.intel.fleetdm.tenant
import tests.data.fleetdm.fleets
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
    cartography.intel.fleetdm.fleets,
    "get",
    return_value=tests.data.fleetdm.fleets.MOCK_FLEETS_RESPONSE["fleets"],
)
def test_sync_fleetdm_fleets(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first (sub_resource_relationship uses OPTIONAL MATCH)
    _create_tenant(neo4j_session)

    # Act
    cartography.intel.fleetdm.fleets.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Fleets exist
    expected_fleets = {
        ("1", "Production"),
        ("2", "Development"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "FleetDMFleet",
            ["id", "name"],
        )
        == expected_fleets
    )

    # Assert Fleets are connected to Tenant via RESOURCE
    expected_rels = {
        ("1", TEST_TENANT_ID),
        ("2", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "FleetDMFleet",
            "id",
            "FleetDMTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.fleetdm.fleets,
    "get",
    return_value=tests.data.fleetdm.fleets.MOCK_FLEETS_RESPONSE["fleets"],
)
def test_fleetdm_fleets_cleanup(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first
    _create_tenant(neo4j_session)

    # Act - load with first update tag
    cartography.intel.fleetdm.fleets.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert - 2 fleets loaded
    initial = check_nodes(neo4j_session, "FleetDMFleet", ["id"])
    assert initial is not None and len(initial) == 2

    # Act - sync with newer tag, empty data
    NEW_UPDATE_TAG = 999999999
    with patch.object(
        cartography.intel.fleetdm.fleets,
        "get",
        return_value=[],
    ):
        cartography.intel.fleetdm.fleets.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            NEW_UPDATE_TAG,
            {"UPDATE_TAG": NEW_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )

    # Assert - stale fleets cleaned up (0 remaining)
    remaining = check_nodes(neo4j_session, "FleetDMFleet", ["id"])
    assert remaining is None or len(remaining) == 0


def test_fleetdm_fleets_sync_skips_on_premium_license_error(neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first, and a pre-existing fleet from a prior sync
    _create_tenant(neo4j_session)
    with patch.object(
        cartography.intel.fleetdm.fleets,
        "get",
        return_value=tests.data.fleetdm.fleets.MOCK_FLEETS_RESPONSE["fleets"],
    ):
        cartography.intel.fleetdm.fleets.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )
    assert len(check_nodes(neo4j_session, "FleetDMFleet", ["id"])) == 2

    # Act - simulate a license downgrade (HTTP 402) on a later sync
    response = requests.Response()
    response.status_code = 402
    with patch.object(
        cartography.intel.fleetdm.fleets,
        "get",
        side_effect=requests.HTTPError(response=response),
    ):
        NEW_UPDATE_TAG = 999999999
        cartography.intel.fleetdm.fleets.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            NEW_UPDATE_TAG,
            {"UPDATE_TAG": NEW_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )

    # Assert - stale fleets from before the license downgrade are cleaned up
    remaining = check_nodes(neo4j_session, "FleetDMFleet", ["id"])
    assert remaining is None or len(remaining) == 0


def test_fleetdm_fleets_sync_reraises_unexpected_http_errors(neo4j_session):
    session = requests.Session()
    _create_tenant(neo4j_session)

    response = requests.Response()
    response.status_code = 500
    with patch.object(
        cartography.intel.fleetdm.fleets,
        "get",
        side_effect=requests.HTTPError(response=response),
    ):
        try:
            cartography.intel.fleetdm.fleets.sync(
                neo4j_session,
                session,
                TEST_TENANT_ID,
                TEST_TENANT_ID,
                TEST_UPDATE_TAG,
                {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
            )
            raised = False
        except requests.HTTPError:
            raised = True

    assert raised
