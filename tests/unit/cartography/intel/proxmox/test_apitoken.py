"""
Tests for Proxmox API token module.
"""

from cartography.intel.proxmox.apitoken import transform_token_data


def test_transform_token_data():
    """Test API token data transformation."""
    raw_tokens = [
        {
            "tokenid": "cartography",
            "userid": "root@pam",
            "expire": 0,
            "privsep": 1,
            "comment": "Read-only automation token",
        },
        {
            "tokenid": "ci",
            "userid": "svc@pve",
            "privsep": 0,
        },
    ]

    cluster_id = "test-cluster"

    result = transform_token_data(raw_tokens, cluster_id)

    assert len(result) == 2

    token1 = result[0]
    assert token1["id"] == "test-cluster/user/root@pam/token/cartography"
    assert token1["tokenid"] == "cartography"
    assert token1["userid"] == "root@pam"
    assert token1["cluster_id"] == cluster_id
    assert token1["expire"] == 0
    assert token1["privsep"] is True
    assert token1["comment"] == "Read-only automation token"

    # privsep=0 should convert to False, and defaults should apply for missing fields
    token2 = result[1]
    assert token2["id"] == "test-cluster/user/svc@pve/token/ci"
    assert token2["expire"] == 0
    assert token2["privsep"] is False
    assert token2["comment"] is None


def test_transform_token_data_empty():
    """Test API token data transformation with empty input."""
    result = transform_token_data([], "test-cluster")
    assert result == []
