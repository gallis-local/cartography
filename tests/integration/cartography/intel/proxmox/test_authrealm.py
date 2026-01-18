"""
Integration tests for Proxmox authentication realm sync.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.authrealm
from cartography.intel.proxmox.authrealm import sync
from tests.data.proxmox.authrealm import MOCK_AUTH_REALM_DATA
from tests.integration.cartography.intel.proxmox import create_test_cluster


TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.authrealm, "get_auth_realms")
def test_authrealm_sync(mock_get_realms, neo4j_session):
    """Test auth realm sync creates ProxmoxAuthRealm nodes and relationships."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock auth realm data
    mock_get_realms.return_value = MOCK_AUTH_REALM_DATA

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - check realms were created
    result = neo4j_session.run(
        """
        MATCH (r:ProxmoxAuthRealm)
        WHERE r.cluster_id = $cluster_id
        RETURN r.id as id, r.realm as realm, r.type as type, r.default as is_default
        ORDER BY r.realm
        """,
        cluster_id=cluster_id,
    )

    realms = list(result)
    assert len(realms) == 4

    # Check PAM realm
    assert realms[2]["id"] == f"{cluster_id}:pam"
    assert realms[2]["realm"] == "pam"
    assert realms[2]["type"] == "pam"
    assert realms[2]["is_default"] is True

    # Check LDAP realm
    assert realms[1]["id"] == f"{cluster_id}:ldap-corp"
    assert realms[1]["realm"] == "ldap-corp"
    assert realms[1]["type"] == "ldap"


@patch.object(cartography.intel.proxmox.authrealm, "get_auth_realms")
def test_authrealm_to_cluster_relationship(mock_get_realms, neo4j_session):
    """Test ProxmoxAuthRealm RESOURCE relationship to ProxmoxCluster."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock auth realm data
    mock_get_realms.return_value = [MOCK_AUTH_REALM_DATA[0]]

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - check relationship exists
    result = neo4j_session.run(
        """
        MATCH (r:ProxmoxAuthRealm)-[:RESOURCE]->(c:ProxmoxCluster)
        WHERE c.id = $cluster_id
        RETURN r.realm as realm, c.id as cluster_id
        """,
        cluster_id=cluster_id,
    )

    rels = list(result)
    assert len(rels) == 1
    assert rels[0]["realm"] == "pam"
    assert rels[0]["cluster_id"] == cluster_id


@patch.object(cartography.intel.proxmox.authrealm, "get_auth_realms")
def test_authrealm_multi_cluster_isolation(mock_get_realms, neo4j_session):
    """Test auth realms from different clusters don't merge."""
    # Setup two clusters
    cluster_a_id = create_test_cluster(neo4j_session, "cluster-a", TEST_UPDATE_TAG)
    cluster_b_id = create_test_cluster(neo4j_session, "cluster-b", TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Same realm name on both clusters
    mock_get_realms.return_value = [MOCK_AUTH_REALM_DATA[0]]

    # Sync to cluster A
    sync(
        neo4j_session,
        proxmox_client,
        cluster_a_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": cluster_a_id},
    )

    # Sync to cluster B
    sync(
        neo4j_session,
        proxmox_client,
        cluster_b_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": cluster_b_id},
    )

    # Assert - should have 2 distinct realms
    result = neo4j_session.run(
        """
        MATCH (r:ProxmoxAuthRealm)
        WHERE r.realm = 'pam'
        RETURN r.id as id, r.cluster_id as cluster_id
        ORDER BY r.id
        """
    )

    realms = list(result)
    assert len(realms) == 2

    # Different cluster IDs
    realm_ids = {r["id"] for r in realms}
    assert f"{cluster_a_id}:pam" in realm_ids
    assert f"{cluster_b_id}:pam" in realm_ids


@patch.object(cartography.intel.proxmox.authrealm, "get_auth_realms")
def test_authrealm_cleanup_stale_data(mock_get_realms, neo4j_session):
    """Test cleanup removes stale auth realms from previous sync."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # First sync - create all realms
    mock_get_realms.return_value = MOCK_AUTH_REALM_DATA

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert first sync created realms
    result = neo4j_session.run(
        """
        MATCH (r:ProxmoxAuthRealm)
        WHERE r.cluster_id = $cluster_id
        RETURN count(r) as count
        """,
        cluster_id=cluster_id,
    )
    assert result.single()["count"] == 4

    # Second sync - only pam and pve remain
    new_update_tag = TEST_UPDATE_TAG + 1
    mock_get_realms.return_value = MOCK_AUTH_REALM_DATA[:2]

    common_job_parameters["UPDATE_TAG"] = new_update_tag

    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        new_update_tag,
        common_job_parameters,
    )

    # Assert stale realms were cleaned up
    result = neo4j_session.run(
        """
        MATCH (r:ProxmoxAuthRealm)
        WHERE r.cluster_id = $cluster_id
        RETURN r.realm as realm
        ORDER BY r.realm
        """,
        cluster_id=cluster_id,
    )

    realms = list(result)
    assert len(realms) == 2
    assert realms[0]["realm"] == "pam"
    assert realms[1]["realm"] == "pve"


@patch.object(cartography.intel.proxmox.authrealm, "get_auth_realms")
def test_authrealm_with_tfa(mock_get_realms, neo4j_session):
    """Test auth realm with two-factor authentication settings."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock auth realm with TFA
    mock_get_realms.return_value = [MOCK_AUTH_REALM_DATA[2]]  # LDAP with TFA

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - check TFA property
    result = neo4j_session.run(
        """
        MATCH (r:ProxmoxAuthRealm)
        WHERE r.cluster_id = $cluster_id AND r.realm = 'ldap-corp'
        RETURN r.tfa as tfa
        """,
        cluster_id=cluster_id,
    )

    realm = result.single()
    assert realm["tfa"] == "oath"
