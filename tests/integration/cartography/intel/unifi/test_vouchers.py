from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.unifi.sites
import cartography.intel.unifi.vouchers
from cartography.intel.unifi.vouchers import sync
from tests.data.unifi import UNIFI_SITES
from tests.data.unifi import UNIFI_VOUCHERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_SITE_ID = "default"


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.vouchers,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_VOUCHERS,
)
async def test_sync_vouchers(mock_get, neo4j_session):
    """
    Test that vouchers sync correctly
    """
    # Arrange
    controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "SITE_ID": TEST_SITE_ID}

    # Act
    await sync(
        neo4j_session, controller, TEST_SITE_ID, TEST_UPDATE_TAG, common_job_parameters
    )

    # Assert
    expected_nodes = {
        ("voucher_001", "12345-67890"),
        ("voucher_002", "98765-43210"),
    }
    assert check_nodes(neo4j_session, "UnifiVoucher", ["id", "code"]) == expected_nodes


@pytest.mark.asyncio
@patch.object(
    cartography.intel.unifi.vouchers,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_VOUCHERS,
)
async def test_sync_vouchers_relationships(mock_get, neo4j_session):
    """
    Test that voucher relationships are created correctly
    """
    # Arrange
    # Create the UnifiSite node first
    neo4j_session.run(
        """
        MERGE (s:UnifiSite{id: $site_id})
        ON CREATE SET s.firstseen = timestamp()
        SET s.name = 'Default', s.lastupdated = $update_tag
        """,
        site_id=TEST_SITE_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "SITE_ID": TEST_SITE_ID}

    # Act
    await sync(
        neo4j_session, controller, TEST_SITE_ID, TEST_UPDATE_TAG, common_job_parameters
    )

    # Assert - Check RESOURCE relationships
    expected_rels = {
        ("voucher_001", TEST_SITE_ID),
        ("voucher_002", TEST_SITE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "UnifiVoucher",
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
    cartography.intel.unifi.vouchers,
    "get",
    new_callable=AsyncMock,
    return_value=UNIFI_VOUCHERS,
)
async def test_sync_vouchers_cleanup(mock_get, neo4j_session):
    """
    Test that stale vouchers are cleaned up
    """
    # Arrange
    # Load the UnifiSite using the actual load function
    cartography.intel.unifi.sites.load_sites(
        neo4j_session,
        UNIFI_SITES,
        TEST_UPDATE_TAG,
    )

    # Create a stale voucher using the load function
    stale_voucher = [
        {
            "id": "stale_voucher",
            "code": "00000-00000",
            "note": "Stale",
            "quota": 0,
            "duration": 480,
            "qos_overwrite": False,
            "qos_usage_quota": None,
            "qos_rate_max_up": None,
            "qos_rate_max_down": None,
            "used": 0,
            "create_time": 1638342818,
            "start_time": None,
            "end_time": None,
            "for_hotspot": False,
            "admin_name": "admin",
            "status": "VALID_MULTI",
            "status_expires": None,
            "site_id": TEST_SITE_ID,
        }
    ]
    cartography.intel.unifi.vouchers.load_vouchers(
        neo4j_session,
        stale_voucher,
        TEST_SITE_ID,
        TEST_UPDATE_TAG - 1,
    )

    controller = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "SITE_ID": TEST_SITE_ID}

    # Act
    await sync(
        neo4j_session, controller, TEST_SITE_ID, TEST_UPDATE_TAG, common_job_parameters
    )

    # Assert - Stale voucher should be removed
    nodes = check_nodes(neo4j_session, "UnifiVoucher", ["id"])
    assert ("stale_voucher",) not in nodes
    assert ("voucher_001",) in nodes
    assert ("voucher_002",) in nodes
