"""
Unit tests for Proxmox snapshot transformation.
"""

from cartography.intel.proxmox.snapshot import transform_snapshot_data
from tests.data.proxmox.snapshot import MOCK_LXC_SNAPSHOTS
from tests.data.proxmox.snapshot import MOCK_QEMU_SNAPSHOTS


def test_transform_qemu_snapshots():
    """Test transforming QEMU VM snapshot data."""
    # Prepare raw snapshot data with VM metadata
    raw_snapshots = []
    for snapshot in MOCK_QEMU_SNAPSHOTS:
        if snapshot["name"] != "current":  # Skip current pseudo-snapshot
            snapshot_copy = snapshot.copy()
            snapshot_copy["node"] = "pve1"
            snapshot_copy["vmid"] = 100
            snapshot_copy["vm_type"] = "qemu"
            raw_snapshots.append(snapshot_copy)

    cluster_id = "cluster1"
    transformed = transform_snapshot_data(raw_snapshots, cluster_id)

    # Should have 2 snapshots (current is filtered in get_snapshots_for_vm)
    assert len(transformed) == 2

    # Check first snapshot
    snap1 = transformed[0]
    assert snap1["id"] == "cluster1/vm/100/snapshot/snapshot1"
    assert snap1["name"] == "snapshot1"
    assert snap1["cluster_id"] == "cluster1"
    assert snap1["vmid"] == 100
    assert snap1["vm_type"] == "qemu"
    assert snap1["node"] == "pve1"
    assert snap1["description"] == "Before system update"
    assert snap1["snaptime"] == 1704067200
    assert snap1["vmstate"] is True
    assert snap1["parent"] == ""

    # Check second snapshot
    snap2 = transformed[1]
    assert snap2["id"] == "cluster1/vm/100/snapshot/snapshot2"
    assert snap2["name"] == "snapshot2"
    assert snap2["vmstate"] is False
    assert snap2["parent"] == "snapshot1"


def test_transform_lxc_snapshots():
    """Test transforming LXC container snapshot data."""
    # Prepare raw snapshot data with VM metadata
    raw_snapshots = []
    for snapshot in MOCK_LXC_SNAPSHOTS:
        if snapshot["name"] != "current":  # Skip current pseudo-snapshot
            snapshot_copy = snapshot.copy()
            snapshot_copy["node"] = "pve1"
            snapshot_copy["vmid"] = 101
            snapshot_copy["vm_type"] = "lxc"
            raw_snapshots.append(snapshot_copy)

    cluster_id = "cluster1"
    transformed = transform_snapshot_data(raw_snapshots, cluster_id)

    # Should have 1 snapshot
    assert len(transformed) == 1

    # Check snapshot
    snap = transformed[0]
    assert snap["id"] == "cluster1/vm/101/snapshot/backup-daily"
    assert snap["name"] == "backup-daily"
    assert snap["cluster_id"] == "cluster1"
    assert snap["vmid"] == 101
    assert snap["vm_type"] == "lxc"
    assert snap["node"] == "pve1"
    assert snap["description"] == "Daily backup"
    assert snap["snaptime"] == 1704067200
    assert snap["vmstate"] is False  # LXC doesn't support vmstate
    assert snap["parent"] == ""


def test_transform_empty_snapshots():
    """Test transforming empty snapshot list."""
    transformed = transform_snapshot_data([], "cluster1")
    assert transformed == []


def test_snapshot_cluster_scoped_id():
    """Test that snapshot IDs are cluster-scoped."""
    raw_snapshots = [
        {
            "name": "test-snap",
            "node": "pve1",
            "vmid": 100,
            "vm_type": "qemu",
            "description": "Test",
            "snaptime": 1704067200,
            "vmstate": 0,
            "parent": "",
        }
    ]

    # Same snapshot on different clusters should have different IDs
    transformed_a = transform_snapshot_data(raw_snapshots, "cluster-a")
    transformed_b = transform_snapshot_data(raw_snapshots, "cluster-b")

    assert transformed_a[0]["id"] == "cluster-a/vm/100/snapshot/test-snap"
    assert transformed_b[0]["id"] == "cluster-b/vm/100/snapshot/test-snap"
    assert transformed_a[0]["id"] != transformed_b[0]["id"]
