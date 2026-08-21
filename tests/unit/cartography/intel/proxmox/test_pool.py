"""
Tests for Proxmox pool module.
"""

from cartography.intel.proxmox.pool import transform_pool_data


def test_transform_pool_data():
    """Test pool data transformation."""
    raw_pools = [
        {"poolid": "production", "comment": "Production workloads"},
        {"poolid": "dev"},
    ]

    cluster_id = "test-cluster"

    result = transform_pool_data(raw_pools, cluster_id)

    assert len(result) == 2

    pool1 = result[0]
    assert pool1["id"] == "test-cluster/pool/production"
    assert pool1["poolid"] == "production"
    assert pool1["comment"] == "Production workloads"
    assert pool1["cluster_id"] == cluster_id

    pool2 = result[1]
    assert pool2["id"] == "test-cluster/pool/dev"
    assert pool2["poolid"] == "dev"
    assert pool2["comment"] is None


def test_transform_pool_data_empty():
    """Test pool data transformation with empty input."""
    result = transform_pool_data([], "test-cluster")
    assert result == []
