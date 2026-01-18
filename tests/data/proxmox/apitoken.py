"""
Mock data for Proxmox API token tests.
"""

# Mock API token data
MOCK_API_TOKEN_DATA = [
    {
        "tokenid": "token1",
        "comment": "Automation token",
        "expire": 0,
        "privsep": 1,
    },
    {
        "tokenid": "token2",
        "comment": "Backup system token",
        "expire": 1735689600,  # Future date: 2025-01-01 00:00:00
        "privsep": 0,
    },
    {
        "tokenid": "readonly-token",
        "comment": "Read-only monitoring",
        "expire": 0,
        "privsep": 1,
    },
]

# Mock users for API token tests
MOCK_USERS_FOR_TOKENS = [
    {
        "userid": "root@pam",
        "enable": 1,
        "email": "root@example.com",
    },
    {
        "userid": "automation@pve",
        "enable": 1,
        "email": "automation@example.com",
    },
]

# Expected transformed API tokens for cluster1, user root@pam
MOCK_API_TOKENS_TRANSFORMED = [
    {
        "id": "cluster1:root@pam:token1",
        "tokenid": "token1",
        "full_tokenid": "root@pam!token1",
        "cluster_id": "cluster1",
        "userid": "root@pam",
        "comment": "Automation token",
        "expire": 0,
        "privsep": True,
    },
    {
        "id": "cluster1:root@pam:token2",
        "tokenid": "token2",
        "full_tokenid": "root@pam!token2",
        "cluster_id": "cluster1",
        "userid": "root@pam",
        "comment": "Backup system token",
        "expire": 1735689600,
        "privsep": False,
    },
]
