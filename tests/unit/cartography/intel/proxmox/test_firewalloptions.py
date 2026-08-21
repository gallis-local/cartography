"""
Tests for Proxmox firewall options module.
"""

from cartography.intel.proxmox.firewalloptions import transform_firewall_options_data


def test_transform_firewall_options_data_cluster_scope():
    """Test firewall options transformation at cluster scope."""
    raw_options = {
        "enable": 1,
        "policy_in": "ACCEPT",
        "policy_out": "ACCEPT",
        "log_level_in": "info",
        "log_level_out": "info",
        "nf_conntrack_max": 262144,
        "nf_conntrack_tcp_timeout_established": 432000,
    }

    result = transform_firewall_options_data(
        raw_options, cluster_id="test-cluster", scope="cluster"
    )

    assert result is not None
    assert result["id"] == "test-cluster/firewall/options"
    assert result["cluster_id"] == "test-cluster"
    assert result["scope"] == "cluster"
    assert result["scope_id"] is None
    assert result["node_id"] is None
    assert result["enable"] is True
    assert result["policy_in"] == "ACCEPT"
    assert result["nf_conntrack_max"] == 262144


def test_transform_firewall_options_data_node_scope():
    """Test firewall options transformation at node scope."""
    raw_options = {"enable": 0}

    result = transform_firewall_options_data(
        raw_options, cluster_id="test-cluster", scope="node", scope_id="node1"
    )

    assert result is not None
    assert result["id"] == "test-cluster/node/node1/firewall/options"
    assert result["scope"] == "node"
    assert result["scope_id"] == "node1"
    assert result["node_id"] == "test-cluster/node/node1"
    assert result["enable"] is False


def test_transform_firewall_options_data_empty_returns_none():
    """Test that empty/falsy options input returns None."""
    assert (
        transform_firewall_options_data({}, cluster_id="test-cluster", scope="cluster")
        is None
    )
