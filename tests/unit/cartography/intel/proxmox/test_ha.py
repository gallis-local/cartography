"""
Tests for Proxmox high availability (HA) module.
"""

from cartography.intel.proxmox.ha import transform_ha_group_data
from cartography.intel.proxmox.ha import transform_ha_resource_data


def test_transform_ha_group_data():
    """Test HA group data transformation."""
    raw_groups = [
        {
            "group": "priority-group",
            "nodes": "node1:2,node2:1",
            "restricted": True,
            "nofailback": False,
            "comment": "Prefer node1",
        },
        {"group": "basic-group"},
    ]

    cluster_id = "test-cluster"

    result = transform_ha_group_data(raw_groups, cluster_id)

    assert len(result) == 2

    group1 = result[0]
    assert group1["id"] == "test-cluster/ha/group/priority-group"
    assert group1["group"] == "priority-group"
    assert group1["cluster_id"] == cluster_id
    assert group1["nodes"] == "node1:2,node2:1"
    assert group1["restricted"] is True
    assert group1["nofailback"] is False

    # Missing optional fields should default sanely
    group2 = result[1]
    assert group2["id"] == "test-cluster/ha/group/basic-group"
    assert group2["nodes"] is None
    assert group2["restricted"] is False
    assert group2["nofailback"] is False
    assert group2["comment"] is None


def test_transform_ha_resource_data():
    """Test HA resource data transformation."""
    raw_resources = [
        {
            "sid": "vm:100",
            "state": "started",
            "group": "priority-group",
            "max_restart": 1,
            "max_relocate": 1,
            "comment": "Critical VM",
        },
        {"sid": "ct:200"},
    ]

    cluster_id = "test-cluster"

    result = transform_ha_resource_data(raw_resources, cluster_id)

    assert len(result) == 2

    resource1 = result[0]
    assert resource1["id"] == "test-cluster/ha/resource/vm:100"
    assert resource1["sid"] == "vm:100"
    assert resource1["cluster_id"] == cluster_id
    assert resource1["state"] == "started"
    assert resource1["group"] == "priority-group"
    assert resource1["max_restart"] == 1
    assert resource1["max_relocate"] == 1

    resource2 = result[1]
    assert resource2["id"] == "test-cluster/ha/resource/ct:200"
    assert resource2["state"] is None
    assert resource2["group"] is None


def test_transform_ha_group_data_empty():
    """Test HA group data transformation with empty input."""
    assert transform_ha_group_data([], "test-cluster") == []


def test_transform_ha_resource_data_empty():
    """Test HA resource data transformation with empty input."""
    assert transform_ha_resource_data([], "test-cluster") == []
