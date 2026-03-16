"""
Integration tests for Proxmox API token sync.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.apitoken
from cartography.intel.proxmox.apitoken import sync
from tests.data.proxmox.apitoken import MOCK_API_TOKEN_DATA
from tests.data.proxmox.apitoken import MOCK_USERS_FOR_TOKENS
from tests.integration.cartography.intel.proxmox import create_test_cluster


TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.apitoken, "get_api_tokens_for_user")
def test_apitoken_sync(mock_get_tokens, neo4j_session):
    """Test API token sync creates ProxmoxAPIToken nodes and relationships."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Create a test user
    neo4j_session.run(
        """
        MERGE (u:ProxmoxUser {id: $user_id})
        SET u.userid = $userid,
            u.cluster_id = $cluster_id,
            u.enable = true
        """,
        user_id=f"{cluster_id}/user/root@pam",
        userid="root@pam",
        cluster_id=cluster_id,
    )

    # Mock API token data
    mock_get_tokens.return_value = MOCK_API_TOKEN_DATA[:2]  # First 2 tokens

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    # Mock users data
    mock_users = [{"userid": "root@pam", "id": f"{cluster_id}/user/root@pam"}]

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
        mock_users,
    )

    # Assert - check tokens were created
    result = neo4j_session.run(
        """
        MATCH (t:ProxmoxAPIToken)
        WHERE t.cluster_id = $cluster_id
        RETURN t.id as id, t.tokenid as tokenid, t.full_tokenid as full_tokenid
        ORDER BY t.tokenid
        """,
        cluster_id=cluster_id,
    )

    tokens = list(result)
    assert len(tokens) == 2

    # Check token 1
    assert tokens[0]["id"] == f"{cluster_id}/user/root@pam/token/token1"
    assert tokens[0]["tokenid"] == "token1"

    # Check token 2
    assert tokens[1]["id"] == f"{cluster_id}/user/root@pam/token/token2"
    assert tokens[1]["tokenid"] == "token2"


@patch.object(cartography.intel.proxmox.apitoken, "get_api_tokens_for_user")
def test_apitoken_to_cluster_relationship(mock_get_tokens, neo4j_session):
    """Test ProxmoxAPIToken RESOURCE relationship to ProxmoxCluster."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Create a test user
    neo4j_session.run(
        """
        MERGE (u:ProxmoxUser {id: $user_id})
        SET u.userid = $userid, u.cluster_id = $cluster_id
        """,
        user_id=f"{cluster_id}/user/root@pam",
        userid="root@pam",
        cluster_id=cluster_id,
    )

    # Mock API token data
    mock_get_tokens.return_value = [MOCK_API_TOKEN_DATA[0]]

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    mock_users = [{"userid": "root@pam", "id": f"{cluster_id}/user/root@pam"}]

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
        mock_users,
    )

    # Assert - check relationship exists
    result = neo4j_session.run(
        """
        MATCH (t:ProxmoxAPIToken)-[:RESOURCE]->(c:ProxmoxCluster)
        WHERE c.id = $cluster_id
        RETURN t.tokenid as tokenid, c.id as cluster_id
        """,
        cluster_id=cluster_id,
    )

    rels = list(result)
    assert len(rels) == 1
    assert rels[0]["tokenid"] == "token1"
    assert rels[0]["cluster_id"] == cluster_id


@patch.object(cartography.intel.proxmox.apitoken, "get_api_tokens_for_user")
def test_apitoken_to_user_relationship(mock_get_tokens, neo4j_session):
    """Test ProxmoxAPIToken BELONGS_TO relationship to ProxmoxUser."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Create a test user
    neo4j_session.run(
        """
        MERGE (u:ProxmoxUser {id: $user_id})
        SET u.userid = $userid,
            u.cluster_id = $cluster_id,
            u.enable = true
        """,
        user_id=f"{cluster_id}/user/root@pam",
        userid="root@pam",
        cluster_id=cluster_id,
    )

    # Mock API token data
    mock_get_tokens.return_value = [MOCK_API_TOKEN_DATA[0]]

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    mock_users = [{"userid": "root@pam", "id": f"{cluster_id}/user/root@pam"}]

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
        mock_users,
    )

    # Assert - check relationship exists
    result = neo4j_session.run(
        """
        MATCH (t:ProxmoxAPIToken)-[:BELONGS_TO]->(u:ProxmoxUser)
        WHERE u.userid = $userid AND u.cluster_id = $cluster_id
        RETURN t.tokenid as tokenid, u.userid as userid
        """,
        userid="root@pam",
        cluster_id=cluster_id,
    )

    rels = list(result)
    assert len(rels) == 1
    assert rels[0]["tokenid"] == "token1"
    assert rels[0]["userid"] == "root@pam"


@patch.object(cartography.intel.proxmox.apitoken, "get_api_tokens_for_user")
def test_apitoken_multi_cluster_isolation(mock_get_tokens, neo4j_session):
    """Test API tokens from different clusters don't merge."""
    # Setup two clusters
    cluster_a_id = create_test_cluster(neo4j_session, "cluster-a", TEST_UPDATE_TAG)
    cluster_b_id = create_test_cluster(neo4j_session, "cluster-b", TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Create test users in both clusters
    for cluster_id in [cluster_a_id, cluster_b_id]:
        neo4j_session.run(
            """
            MERGE (u:ProxmoxUser {id: $user_id})
            SET u.userid = $userid, u.cluster_id = $cluster_id
            """,
            user_id=f"{cluster_id}/user/root@pam",
            userid="root@pam",
            cluster_id=cluster_id,
        )

    # Same token name on both clusters
    mock_get_tokens.return_value = [MOCK_API_TOKEN_DATA[0]]

    # Sync to cluster A
    mock_users_a = [{"userid": "root@pam", "id": f"{cluster_a_id}/user/root@pam"}]
    sync(
        neo4j_session,
        proxmox_client,
        cluster_a_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": cluster_a_id},
        mock_users_a,
    )

    # Sync to cluster B
    mock_users_b = [{"userid": "root@pam", "id": f"{cluster_b_id}/user/root@pam"}]
    sync(
        neo4j_session,
        proxmox_client,
        cluster_b_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": cluster_b_id},
        mock_users_b,
    )

    # Assert - should have 2 distinct tokens
    result = neo4j_session.run(
        """
        MATCH (t:ProxmoxAPIToken)
        WHERE t.tokenid = 'token1'
        RETURN t.id as id, t.cluster_id as cluster_id
        ORDER BY t.id
        """
    )

    tokens = list(result)
    assert len(tokens) == 2

    # Different cluster IDs
    token_ids = {t["id"] for t in tokens}
    assert f"{cluster_a_id}/user/root@pam/token/token1" in token_ids
    assert f"{cluster_b_id}/user/root@pam/token/token1" in token_ids


@patch.object(cartography.intel.proxmox.apitoken, "get_api_tokens_for_user")
def test_apitoken_cleanup_stale_data(mock_get_tokens, neo4j_session):
    """Test cleanup removes stale API tokens from previous sync."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Create a test user
    neo4j_session.run(
        """
        MERGE (u:ProxmoxUser {id: $user_id})
        SET u.userid = $userid, u.cluster_id = $cluster_id
        """,
        user_id=f"{cluster_id}/user/root@pam",
        userid="root@pam",
        cluster_id=cluster_id,
    )

    # First sync - create token1 and token2
    mock_get_tokens.return_value = MOCK_API_TOKEN_DATA[:2]

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    mock_users = [{"userid": "root@pam", "id": f"{cluster_id}/user/root@pam"}]

    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
        mock_users,
    )

    # Assert first sync created tokens
    result = neo4j_session.run(
        """
        MATCH (t:ProxmoxAPIToken)
        WHERE t.cluster_id = $cluster_id
        RETURN count(t) as count
        """,
        cluster_id=cluster_id,
    )
    assert result.single()["count"] == 2

    # Second sync - only token1 remains
    new_update_tag = TEST_UPDATE_TAG + 1
    mock_get_tokens.return_value = [MOCK_API_TOKEN_DATA[0]]

    common_job_parameters["UPDATE_TAG"] = new_update_tag

    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        new_update_tag,
        common_job_parameters,
        mock_users,
    )

    # Assert stale token2 was cleaned up
    result = neo4j_session.run(
        """
        MATCH (t:ProxmoxAPIToken)
        WHERE t.cluster_id = $cluster_id
        RETURN t.tokenid as tokenid
        """,
        cluster_id=cluster_id,
    )

    tokens = list(result)
    assert len(tokens) == 1
    assert tokens[0]["tokenid"] == "token1"
