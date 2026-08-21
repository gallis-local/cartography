"""
Tests for Proxmox replication module.
"""

from cartography.intel.proxmox.replication import transform_replication_job_data


def test_transform_replication_job_data():
    """Test replication job data transformation."""
    raw_jobs = [
        {
            "id": "100-0",
            "guest": 100,
            "target": "node2",
            "source": "node1",
            "type": "local",
            "schedule": "*/15",
            "rate": 10,
            "disable": 0,
            "comment": "Replicate to node2",
        },
        {
            "id": "200-0",
            "guest": 200,
            "target": "node3",
            "disable": 1,
        },
    ]

    cluster_id = "test-cluster"

    result = transform_replication_job_data(raw_jobs, cluster_id)

    assert len(result) == 2

    job1 = result[0]
    assert job1["id"] == "test-cluster/replication/100-0"
    assert job1["job_id"] == "100-0"
    assert job1["cluster_id"] == cluster_id
    assert job1["guest"] == 100
    assert job1["target"] == "node2"
    assert job1["target_node_id"] == "test-cluster/node/node2"
    assert job1["source"] == "node1"
    assert job1["source_node_id"] == "test-cluster/node/node1"
    assert job1["disable"] is False

    # No source provided -> source_node_id should be None; disable=1 -> True
    job2 = result[1]
    assert job2["id"] == "test-cluster/replication/200-0"
    assert job2["source"] is None
    assert job2["source_node_id"] is None
    assert job2["target_node_id"] == "test-cluster/node/node3"
    assert job2["disable"] is True


def test_transform_replication_job_data_empty():
    """Test replication job data transformation with empty input."""
    result = transform_replication_job_data([], "test-cluster")
    assert result == []
