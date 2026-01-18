"""
Mock data for Proxmox replication job tests.
"""

# Mock replication job data
MOCK_REPLICATION_JOB_DATA = [
    {
        "id": "100-0",
        "type": "local",
        "target": "pve2",
        "guest": 100,
        "schedule": "*/15",
        "rate": 10,
        "comment": "VM replication to pve2",
        "enabled": 1,
        "source": "pve1",
    },
    {
        "id": "101-0",
        "type": "local",
        "target": "pve3",
        "guest": 101,
        "schedule": "*/30",
        "comment": "Container replication",
        "enabled": 1,
        "source": "pve1",
    },
    {
        "id": "102-0",
        "type": "local",
        "target": "pve2",
        "guest": 102,
        "schedule": "0 1 * * *",
        "comment": "Daily replication",
        "enabled": 0,
        "source": "pve1",
    },
]

# Expected transformed replication jobs for cluster1
MOCK_REPLICATION_JOBS_TRANSFORMED = [
    {
        "id": "cluster1:100-0",
        "job_id": "100-0",
        "cluster_id": "cluster1",
        "type": "local",
        "target": "pve2",
        "guest": 100,
        "schedule": "*/15",
        "rate": 10,
        "comment": "VM replication to pve2",
        "enabled": True,
        "source": "pve1",
    },
    {
        "id": "cluster1:101-0",
        "job_id": "101-0",
        "cluster_id": "cluster1",
        "type": "local",
        "target": "pve3",
        "guest": 101,
        "schedule": "*/30",
        "rate": None,
        "comment": "Container replication",
        "enabled": True,
        "source": "pve1",
    },
    {
        "id": "cluster1:102-0",
        "job_id": "102-0",
        "cluster_id": "cluster1",
        "type": "local",
        "target": "pve2",
        "guest": 102,
        "schedule": "0 1 * * *",
        "rate": None,
        "comment": "Daily replication",
        "enabled": False,
        "source": "pve1",
    },
]
