"""
Mock data for Proxmox snapshot tests.
"""

# Mock snapshot data for a QEMU VM (vmid 100)
MOCK_QEMU_SNAPSHOTS = [
    {
        "name": "snapshot1",
        "description": "Before system update",
        "snaptime": 1704067200,  # 2024-01-01 00:00:00
        "vmstate": 1,
        "parent": "",
    },
    {
        "name": "snapshot2",
        "description": "After system update",
        "snaptime": 1704153600,  # 2024-01-02 00:00:00
        "vmstate": 0,
        "parent": "snapshot1",
    },
    {
        "name": "current",  # This should be filtered out
        "description": "Current state",
    },
]

# Mock snapshot data for an LXC container (vmid 101)
MOCK_LXC_SNAPSHOTS = [
    {
        "name": "backup-daily",
        "description": "Daily backup",
        "snaptime": 1704067200,
        "parent": "",
    },
    {
        "name": "current",  # This should be filtered out
        "description": "Current state",
    },
]

# Expected transformed snapshots for QEMU VM on cluster1, node pve1
MOCK_QEMU_SNAPSHOTS_TRANSFORMED = [
    {
        "id": "cluster1:pve1/qemu/100:snapshot1",
        "name": "snapshot1",
        "cluster_id": "cluster1",
        "vmid": 100,
        "vm_type": "qemu",
        "node": "pve1",
        "description": "Before system update",
        "snaptime": 1704067200,
        "vmstate": True,
        "parent": "",
    },
    {
        "id": "cluster1:pve1/qemu/100:snapshot2",
        "name": "snapshot2",
        "cluster_id": "cluster1",
        "vmid": 100,
        "vm_type": "qemu",
        "node": "pve1",
        "description": "After system update",
        "snaptime": 1704153600,
        "vmstate": False,
        "parent": "snapshot1",
    },
]

# Expected transformed snapshots for LXC container on cluster1, node pve1
MOCK_LXC_SNAPSHOTS_TRANSFORMED = [
    {
        "id": "cluster1:pve1/lxc/101:backup-daily",
        "name": "backup-daily",
        "cluster_id": "cluster1",
        "vmid": 101,
        "vm_type": "lxc",
        "node": "pve1",
        "description": "Daily backup",
        "snaptime": 1704067200,
        "vmstate": False,
        "parent": "",
    },
]

# Mock VM list for snapshot sync
MOCK_VMS_FOR_SNAPSHOT = [
    {
        "node": "pve1",
        "vmid": 100,
        "type": "qemu",
        "name": "test-vm",
        "status": "running",
    },
    {
        "node": "pve1",
        "vmid": 101,
        "type": "lxc",
        "name": "test-container",
        "status": "running",
    },
]
