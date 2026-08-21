from unittest.mock import patch

import neo4j
import requests

import cartography.intel.fleetdm.labels
import cartography.intel.fleetdm.tenant
import tests.data.fleetdm.labels
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
    cartography.intel.fleetdm.labels,
    "get",
    return_value=tests.data.fleetdm.labels.MOCK_LABELS_RESPONSE["labels"],
)
def test_sync_fleetdm_labels(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first (sub_resource_relationship uses OPTIONAL MATCH)
    _create_tenant(neo4j_session)

    # Act
    cartography.intel.fleetdm.labels.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Labels exist
    expected_labels = {
        ("1", "All Hosts"),
        ("2", "macOS"),
        ("3", "Ubuntu Linux"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "FleetDMLabel",
            ["id", "name"],
        )
        == expected_labels
    )

    # Assert Labels are connected to Tenant via RESOURCE
    expected_rels = {
        ("1", TEST_TENANT_ID),
        ("2", TEST_TENANT_ID),
        ("3", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "FleetDMLabel",
            "id",
            "FleetDMTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.fleetdm.labels,
    "get",
    return_value=tests.data.fleetdm.labels.MOCK_LABELS_RESPONSE["labels"],
)
def test_fleetdm_labels_cleanup(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first
    _create_tenant(neo4j_session)

    # Act - load with first update tag
    cartography.intel.fleetdm.labels.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert - 3 labels loaded
    initial = check_nodes(neo4j_session, "FleetDMLabel", ["id"])
    assert initial is not None and len(initial) == 3

    # Act - sync with newer tag, empty data
    NEW_UPDATE_TAG = 999999999
    with patch.object(
        cartography.intel.fleetdm.labels,
        "get",
        return_value=[],
    ):
        cartography.intel.fleetdm.labels.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            NEW_UPDATE_TAG,
            {"UPDATE_TAG": NEW_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )

    # Assert - stale labels cleaned up (0 remaining)
    remaining = check_nodes(neo4j_session, "FleetDMLabel", ["id"])
    assert remaining is None or len(remaining) == 0
