"""
Integration tests for multi-cluster Proxmox deployments.

Tests that entities from different clusters don't merge and remain properly isolated.
"""

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox
import cartography.intel.proxmox.access
import cartography.intel.proxmox.cluster
import cartography.intel.proxmox.compute
from tests.data.proxmox.access import MOCK_USER_DATA
from tests.data.proxmox.cluster import MOCK_CLUSTER_DATA
from tests.data.proxmox.cluster import MOCK_NODE_DATA
from tests.data.proxmox.compute import MOCK_VM_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_A = "cluster-a"
TEST_CLUSTER_B = "cluster-b"

MOCK_NODES = [
    {"node": "pve1"},  # Same node name in both clusters
]

MOCK_VM_DATA_MULTI = {
    "pve1": [
        {"vmid": 100, "name": "vm-100", "type": "qemu", "node": "pve1"},  # Same VMID in both clusters
    ]
}


@patch.object(cartography.intel.proxmox.cluster, "get_cluster_status", return_value=MOCK_CLUSTER_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_cluster_options", return_value={})
@patch.object(cartography.intel.proxmox.cluster, "get_cluster_config", return_value={})
@patch.object(cartography.intel.proxmox.cluster, "get_node_network", return_value=[])
@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node", return_value=[])
@patch.object(cartography.intel.proxmox.compute, "get_vm_config", return_value={})
@patch.object(cartography.intel.proxmox.access, "get_users")
def test_multi_cluster_node_isolation(
    mock_get_users,
    mock_get_vm_config,
    mock_get_containers,
    mock_get_vms,
    mock_get_node_network,
    mock_get_config,
    mock_get_options,
    mock_get_nodes,
    mock_get_cluster,
    neo4j_session,
):
    """
    Test that nodes with the same name in different clusters don't merge.
    """
    # Arrange
    proxmox_a = MagicMock()
    proxmox_a.nodes.get.return_value = MOCK_NODES

    proxmox_b = MagicMock()
    proxmox_b.nodes.get.return_value = MOCK_NODES

    mock_get_vms.return_value = []
    mock_get_users.return_value = []

    common_params_a: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_A,
    }

    common_params_b: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_B,
    }

    # Act - Sync cluster A
    cartography.intel.proxmox.cluster.sync(
        neo4j_session,
        proxmox_a,
        TEST_CLUSTER_A,
        TEST_UPDATE_TAG,
        common_params_a,
    )

    # Act - Sync cluster B with same node names
    cartography.intel.proxmox.cluster.sync(
        neo4j_session,
        proxmox_b,
        TEST_CLUSTER_B,
        TEST_UPDATE_TAG,
        common_params_b,
    )

    # Assert - Should have 2 separate ProxmoxNode nodes
    # check_nodes returns a set of tuples: {(id, name, cluster_id), ...}
    nodes = check_nodes(
        neo4j_session,
        "ProxmoxNode",
        ["id", "name", "cluster_id"],
    )

    assert len(nodes) == 2, f"Expected 2 nodes, got {len(nodes)}"

    # Unpack tuple elements by position (id=0, name=1, cluster_id=2)
    node_ids = {node[0] for node in nodes}
    node_names = {node[1] for node in nodes}
    cluster_ids = {node[2] for node in nodes}

    assert len(node_ids) == 2, f"Node IDs should be unique: {node_ids}"
    assert len(node_names) == 1, f"Node names should be the same: {node_names}"
    assert "pve1" in node_names, f"Expected node name 'pve1', got {node_names}"
    assert len(cluster_ids) == 2, f"Nodes should belong to different clusters: {cluster_ids}"
    assert TEST_CLUSTER_A in cluster_ids
    assert TEST_CLUSTER_B in cluster_ids

    # Verify cluster-scoped IDs
    expected_ids = {f"{TEST_CLUSTER_A}/node/pve1", f"{TEST_CLUSTER_B}/node/pve1"}
    assert node_ids == expected_ids, f"Expected {expected_ids}, got {node_ids}"


@patch.object(cartography.intel.proxmox.cluster, "get_cluster_status", return_value=MOCK_CLUSTER_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_cluster_options", return_value={})
@patch.object(cartography.intel.proxmox.cluster, "get_cluster_config", return_value={})
@patch.object(cartography.intel.proxmox.cluster, "get_node_network", return_value=[])
@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node", return_value=[])
@patch.object(cartography.intel.proxmox.compute, "get_vm_config", return_value={})
def test_multi_cluster_vm_isolation(
    mock_get_vm_config,
    mock_get_containers,
    mock_get_vms,
    mock_get_node_network,
    mock_get_config,
    mock_get_options,
    mock_get_nodes,
    mock_get_cluster,
    neo4j_session,
):
    """
    Test that VMs with the same VMID in different clusters don't merge.
    """
    # Arrange
    proxmox_a = MagicMock()
    proxmox_a.nodes.get.return_value = MOCK_NODES

    proxmox_b = MagicMock()
    proxmox_b.nodes.get.return_value = MOCK_NODES

    def get_vms_side_effect(proxmox_client, node_name):
        return [vm for vm in MOCK_VM_DATA_MULTI.get(node_name, []) if vm.get("type") == "qemu"]

    mock_get_vms.side_effect = get_vms_side_effect

    common_params_a: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_A,
    }

    common_params_b: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_B,
    }

    # Act - Sync both clusters
    cartography.intel.proxmox.sync(
        neo4j_session,
        proxmox_a,
        TEST_CLUSTER_A,
        TEST_UPDATE_TAG,
        common_params_a,
    )

    cartography.intel.proxmox.sync(
        neo4j_session,
        proxmox_b,
        TEST_CLUSTER_B,
        TEST_UPDATE_TAG,
        common_params_b,
    )

    # Assert - Should have 2 separate ProxmoxVM nodes
    # check_nodes returns a set of tuples: {(id, vmid, name, cluster_id), ...}
    vms = check_nodes(
        neo4j_session,
        "ProxmoxVM",
        ["id", "vmid", "name", "cluster_id"],
    )

    assert len(vms) == 2, f"Expected 2 VMs, got {len(vms)}"

    # Unpack tuple elements by position (id=0, vmid=1, name=2, cluster_id=3)
    vm_ids = {vm[0] for vm in vms}
    vm_vmids = {vm[1] for vm in vms}
    vm_names = {vm[2] for vm in vms}
    cluster_ids = {vm[3] for vm in vms}

    assert len(vm_ids) == 2, f"VM IDs should be unique: {vm_ids}"
    assert len(vm_vmids) == 1, f"VM VMIDs should be the same: {vm_vmids}"
    assert 100 in vm_vmids, f"Expected VMID 100, got {vm_vmids}"
    assert len(vm_names) == 1, f"VM names should be the same: {vm_names}"
    assert "vm-100" in vm_names, f"Expected VM name 'vm-100', got {vm_names}"
    assert len(cluster_ids) == 2, f"VMs should belong to different clusters: {cluster_ids}"
    assert TEST_CLUSTER_A in cluster_ids
    assert TEST_CLUSTER_B in cluster_ids

    # Verify cluster-scoped IDs
    expected_id_a = f"{TEST_CLUSTER_A}/vm/100"
    expected_id_b = f"{TEST_CLUSTER_B}/vm/100"
    expected_ids = {expected_id_a, expected_id_b}
    assert vm_ids == expected_ids, f"Expected {expected_ids}, got {vm_ids}"


@patch.object(cartography.intel.proxmox.access, "get_users")
@patch.object(cartography.intel.proxmox.access, "get_groups", return_value=[])
@patch.object(cartography.intel.proxmox.access, "get_roles", return_value=[])
@patch.object(cartography.intel.proxmox.access, "get_acls", return_value=[])
def test_multi_cluster_user_isolation(
    mock_get_acls,
    mock_get_roles,
    mock_get_groups,
    mock_get_users,
    neo4j_session,
):
    """
    Test that users with the same userid in different clusters don't merge.
    """
    # Arrange
    proxmox_a = MagicMock()
    proxmox_b = MagicMock()

    # Same user in both clusters
    mock_get_users.return_value = MOCK_USER_DATA[:1]  # Just root@pam

    common_params_a: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_A,
    }

    common_params_b: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_B,
    }

    # Act - Sync both clusters
    cartography.intel.proxmox.access.sync(
        neo4j_session,
        proxmox_a,
        TEST_CLUSTER_A,
        TEST_UPDATE_TAG,
        common_params_a,
    )

    cartography.intel.proxmox.access.sync(
        neo4j_session,
        proxmox_b,
        TEST_CLUSTER_B,
        TEST_UPDATE_TAG,
        common_params_b,
    )

    # Assert - Should have 2 separate ProxmoxUser nodes
    # check_nodes returns a set of tuples: {(id, userid, cluster_id), ...}
    users = check_nodes(
        neo4j_session,
        "ProxmoxUser",
        ["id", "userid", "cluster_id"],
    )

    assert len(users) == 2, f"Expected 2 users, got {len(users)}"

    # Unpack tuple elements by position (id=0, userid=1, cluster_id=2)
    user_ids = {user[0] for user in users}
    userids = {user[1] for user in users}
    cluster_ids = {user[2] for user in users}

    assert len(user_ids) == 2, f"User IDs should be unique: {user_ids}"
    assert len(userids) == 1, f"User userids should be the same: {userids}"
    assert len(cluster_ids) == 2, f"Users should belong to different clusters: {cluster_ids}"
    assert TEST_CLUSTER_A in cluster_ids
    assert TEST_CLUSTER_B in cluster_ids

    # Verify cluster-scoped IDs
    userid = MOCK_USER_DATA[0]["userid"]
    expected_ids = {f"{TEST_CLUSTER_A}/user/{userid}", f"{TEST_CLUSTER_B}/user/{userid}"}
    assert user_ids == expected_ids, f"Expected {expected_ids}, got {user_ids}"


@patch.object(cartography.intel.proxmox.cluster, "get_cluster_status", return_value=MOCK_CLUSTER_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_cluster_options", return_value={})
@patch.object(cartography.intel.proxmox.cluster, "get_cluster_config", return_value={})
@patch.object(cartography.intel.proxmox.cluster, "get_node_network", return_value=[])
@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node", return_value=[])
@patch.object(cartography.intel.proxmox.compute, "get_vm_config", return_value={})
def test_multi_cluster_network_adjacency_isolation(
    mock_get_vm_config,
    mock_get_containers,
    mock_get_vms,
    mock_get_node_network,
    mock_get_config,
    mock_get_options,
    mock_get_nodes,
    mock_get_cluster,
    neo4j_session,
):
    """
    Test that NETWORK_ADJACENT relationships don't cross cluster boundaries.

    VMs on the same bridge/VLAN in different clusters should NOT be adjacent.
    """
    # Arrange
    proxmox_a = MagicMock()
    proxmox_a.nodes.get.return_value = MOCK_NODES

    proxmox_b = MagicMock()
    proxmox_b.nodes.get.return_value = MOCK_NODES

    # VMs on same bridge in both clusters
    mock_vm_data = {
        "pve1": [
            {
                "vmid": 100,
                "name": "vm-100",
                "type": "qemu",
                "node": "pve1",
                "net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr0",
            },
            {
                "vmid": 101,
                "name": "vm-101",
                "type": "qemu",
                "node": "pve1",
                "net0": "virtio=AA:BB:CC:DD:EE:02,bridge=vmbr0",
            },
        ]
    }

    def get_vms_side_effect(proxmox_client, node_name):
        return [vm for vm in mock_vm_data.get(node_name, []) if vm.get("type") == "qemu"]

    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        for vm in mock_vm_data.get(node, []):
            if vm["vmid"] == vmid:
                return vm
        return {}

    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect

    common_params_a: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_A,
    }

    common_params_b: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_B,
    }

    # Act - Sync both clusters
    cartography.intel.proxmox.sync(
        neo4j_session,
        proxmox_a,
        TEST_CLUSTER_A,
        TEST_UPDATE_TAG,
        common_params_a,
    )

    cartography.intel.proxmox.sync(
        neo4j_session,
        proxmox_b,
        TEST_CLUSTER_B,
        TEST_UPDATE_TAG,
        common_params_b,
    )

    # Assert - Should have 4 VMs total (2 per cluster)
    # check_nodes returns a set of tuples: {(id, vmid, cluster_id), ...}
    vms = check_nodes(
        neo4j_session,
        "ProxmoxVM",
        ["id", "vmid", "cluster_id"],
    )

    assert len(vms) == 4, f"Expected 4 VMs, got {len(vms)}"

    # Check NETWORK_ADJACENT relationships using raw Cypher
    # (check_rels doesn't support relationship property filters)
    result = neo4j_session.run(
        """
        MATCH (vm1:ProxmoxVM)-[:NETWORK_ADJACENT]->(vm2:ProxmoxVM)
        RETURN vm1.cluster_id AS cluster1, vm2.cluster_id AS cluster2
        ORDER BY cluster1
        """
    )
    adjacency_rels = list(result)

    # Each cluster should have 1 adjacency relationship between its 2 VMs
    assert len(adjacency_rels) == 2, f"Expected 2 NETWORK_ADJACENT relationships, got {len(adjacency_rels)}"

    # Verify no cross-cluster relationships
    for rel in adjacency_rels:
        assert rel["cluster1"] == rel["cluster2"], (
            f"NETWORK_ADJACENT relationship crosses cluster boundary: "
            f"{rel['cluster1']} -> {rel['cluster2']}"
        )
