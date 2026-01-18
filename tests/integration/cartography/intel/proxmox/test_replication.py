"""
Integration tests for Proxmox replication job sync.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.replication
from cartography.intel.proxmox.replication import sync
from tests.data.proxmox.replication import MOCK_REPLICATION_JOB_DATA
from tests.integration.cartography.intel.proxmox import create_test_cluster


TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.replication, "get_replication_jobs")
def test_replication_sync(mock_get_jobs, neo4j_session):
    """Test replication job sync creates ProxmoxReplicationJob nodes and relationships."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock replication job data
    mock_get_jobs.return_value = MOCK_REPLICATION_JOB_DATA

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

    # Assert - check jobs were created
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxReplicationJob)
        WHERE j.cluster_id = $cluster_id
        RETURN j.id as id, j.job_id as job_id, j.guest as guest, j.target as target
        ORDER BY j.job_id
        """,
        cluster_id=cluster_id,
    )

    jobs = list(result)
    assert len(jobs) == 3

    # Check job 1
    assert jobs[0]["id"] == f"{cluster_id}:100-0"
    assert jobs[0]["job_id"] == "100-0"
    assert jobs[0]["guest"] == 100
    assert jobs[0]["target"] == "pve2"

    # Check job 2
    assert jobs[1]["id"] == f"{cluster_id}:101-0"
    assert jobs[1]["guest"] == 101


@patch.object(cartography.intel.proxmox.replication, "get_replication_jobs")
def test_replication_to_cluster_relationship(mock_get_jobs, neo4j_session):
    """Test ProxmoxReplicationJob RESOURCE relationship to ProxmoxCluster."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock replication job data
    mock_get_jobs.return_value = [MOCK_REPLICATION_JOB_DATA[0]]

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
        MATCH (j:ProxmoxReplicationJob)-[:RESOURCE]->(c:ProxmoxCluster)
        WHERE c.id = $cluster_id
        RETURN j.job_id as job_id, c.id as cluster_id
        """,
        cluster_id=cluster_id,
    )

    rels = list(result)
    assert len(rels) == 1
    assert rels[0]["job_id"] == "100-0"
    assert rels[0]["cluster_id"] == cluster_id


@patch.object(cartography.intel.proxmox.replication, "get_replication_jobs")
def test_replication_multi_cluster_isolation(mock_get_jobs, neo4j_session):
    """Test replication jobs from different clusters don't merge."""
    # Setup two clusters
    cluster_a_id = create_test_cluster(neo4j_session, "cluster-a", TEST_UPDATE_TAG)
    cluster_b_id = create_test_cluster(neo4j_session, "cluster-b", TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Same job ID on both clusters
    mock_get_jobs.return_value = [MOCK_REPLICATION_JOB_DATA[0]]

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

    # Assert - should have 2 distinct jobs
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxReplicationJob)
        WHERE j.job_id = '100-0'
        RETURN j.id as id, j.cluster_id as cluster_id
        ORDER BY j.id
        """
    )

    jobs = list(result)
    assert len(jobs) == 2

    # Different cluster IDs
    job_ids = {j["id"] for j in jobs}
    assert f"{cluster_a_id}:100-0" in job_ids
    assert f"{cluster_b_id}:100-0" in job_ids


@patch.object(cartography.intel.proxmox.replication, "get_replication_jobs")
def test_replication_cleanup_stale_data(mock_get_jobs, neo4j_session):
    """Test cleanup removes stale replication jobs from previous sync."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # First sync - create all jobs
    mock_get_jobs.return_value = MOCK_REPLICATION_JOB_DATA

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

    # Assert first sync created jobs
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxReplicationJob)
        WHERE j.cluster_id = $cluster_id
        RETURN count(j) as count
        """,
        cluster_id=cluster_id,
    )
    assert result.single()["count"] == 3

    # Second sync - only first job remains
    new_update_tag = TEST_UPDATE_TAG + 1
    mock_get_jobs.return_value = [MOCK_REPLICATION_JOB_DATA[0]]

    common_job_parameters["UPDATE_TAG"] = new_update_tag

    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        new_update_tag,
        common_job_parameters,
    )

    # Assert stale jobs were cleaned up
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxReplicationJob)
        WHERE j.cluster_id = $cluster_id
        RETURN j.job_id as job_id
        """,
        cluster_id=cluster_id,
    )

    jobs = list(result)
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == "100-0"


@patch.object(cartography.intel.proxmox.replication, "get_replication_jobs")
def test_replication_enabled_disabled(mock_get_jobs, neo4j_session):
    """Test replication job enabled/disabled status."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock replication job data with one enabled and one disabled
    mock_get_jobs.return_value = [
        MOCK_REPLICATION_JOB_DATA[0],  # enabled
        MOCK_REPLICATION_JOB_DATA[2],  # disabled
    ]

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

    # Assert - check enabled status
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxReplicationJob)
        WHERE j.cluster_id = $cluster_id
        RETURN j.job_id as job_id, j.enabled as enabled
        ORDER BY j.job_id
        """,
        cluster_id=cluster_id,
    )

    jobs = list(result)
    assert len(jobs) == 2
    assert jobs[0]["job_id"] == "100-0"
    assert jobs[0]["enabled"] is True
    assert jobs[1]["job_id"] == "102-0"
    assert jobs[1]["enabled"] is False
