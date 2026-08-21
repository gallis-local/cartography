"""
Tests for Proxmox authentication realm module.
"""

from cartography.intel.proxmox.authrealm import transform_auth_realm_data


def test_transform_auth_realm_data():
    """Test auth realm data transformation."""
    raw_realms = [
        {
            "realm": "pam",
            "type": "pam",
            "comment": "Linux PAM",
            "default": 1,
        },
        {
            "realm": "ad",
            "type": "ad",
            "tfa": "oath",
        },
    ]

    cluster_id = "test-cluster"

    result = transform_auth_realm_data(raw_realms, cluster_id)

    assert len(result) == 2

    realm1 = result[0]
    assert realm1["id"] == "test-cluster/realm/pam"
    assert realm1["realm"] == "pam"
    assert realm1["cluster_id"] == cluster_id
    assert realm1["type"] == "pam"
    assert realm1["comment"] == "Linux PAM"
    assert realm1["default"] is True
    assert realm1["tfa"] is None

    # default should be False when absent, tfa should pass through
    realm2 = result[1]
    assert realm2["id"] == "test-cluster/realm/ad"
    assert realm2["default"] is False
    assert realm2["tfa"] == "oath"


def test_transform_auth_realm_data_empty():
    """Test auth realm data transformation with empty input."""
    result = transform_auth_realm_data([], "test-cluster")
    assert result == []
