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
