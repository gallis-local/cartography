"""
Mock data for Proxmox firewall options tests.
"""

# Mock cluster-level firewall options data
MOCK_CLUSTER_FIREWALL_OPTIONS = {
    "enable": 1,
    "policy_in": "DROP",
    "policy_out": "ACCEPT",
    "log_level_in": "info",
    "log_level_out": "warning",
    "nf_conntrack_max": 262144,
    "nf_conntrack_tcp_timeout_established": 432000,
}

# Mock node-level firewall options data
MOCK_NODE_FIREWALL_OPTIONS = {
    "enable": 1,
    "policy_in": "ACCEPT",
    "policy_out": "ACCEPT",
    "log_level_in": "nolog",
    "log_level_out": "nolog",
}

# Expected transformed cluster-level firewall options for cluster1
MOCK_CLUSTER_FIREWALL_OPTIONS_TRANSFORMED = {
    "id": "cluster1:cluster:firewall_options",
    "cluster_id": "cluster1",
    "scope": "cluster",
    "scope_id": None,
    "enable": True,
    "policy_in": "DROP",
    "policy_out": "ACCEPT",
    "log_level_in": "info",
    "log_level_out": "warning",
    "nf_conntrack_max": 262144,
    "nf_conntrack_tcp_timeout_established": 432000,
}

# Expected transformed node-level firewall options for cluster1, node pve1
MOCK_NODE_FIREWALL_OPTIONS_TRANSFORMED = {
    "id": "cluster1:node:pve1:firewall_options",
    "cluster_id": "cluster1",
    "scope": "node",
    "scope_id": "pve1",
    "enable": True,
    "policy_in": "ACCEPT",
    "policy_out": "ACCEPT",
    "log_level_in": "nolog",
    "log_level_out": "nolog",
    "nf_conntrack_max": None,
    "nf_conntrack_tcp_timeout_established": None,
}
