"""
Integration tests for Proxmox snapshot sync.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.snapshot
from cartography.intel.proxmox.snapshot import sync
from tests.data.proxmox.snapshot import MOCK_LXC_SNAPSHOTS
from tests.data.proxmox.snapshot import MOCK_QEMU_SNAPSHOTS
from tests.data.proxmox.snapshot import MOCK_VMS_FOR_SNAPSHOT
from tests.integration.cartography.intel.proxmox import create_test_cluster


TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.snapshot, "get_all_snapshots")
def test_snapshot_sync(mock_get_snapshots, neo4j_session):
    """Test snapshot sync creates ProxmoxSnapshot nodes and relationships."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock snapshot data
    mock_snapshot_data = []
    for snapshot in MOCK_QEMU_SNAPSHOTS:
        if snapshot["name"] != "current":
            snapshot_copy = snapshot.copy()
            snapshot_copy["node"] = "pve1"
            snapshot_copy["vmid"] = 100
            snapshot_copy["vm_type"] = "qemu"
            mock_snapshot_data.append(snapshot_copy)

    mock_get_snapshots.return_value = mock_snapshot_data

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
        MOCK_VMS_FOR_SNAPSHOT,
    )

    # Assert - check snapshots were created
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxSnapshot)
        WHERE s.cluster_id = $cluster_id
        RETURN s.id as id, s.name as name, s.vmid as vmid, s.vm_type as vm_type
        ORDER BY s.name
        """,
        cluster_id=cluster_id,
    )

    snapshots = list(result)
    assert len(snapshots) == 2

    # Check snapshot 1
    assert snapshots[0]["id"] == f"{cluster_id}:pve1/qemu/100:snapshot1"
    assert snapshots[0]["name"] == "snapshot1"
    assert snapshots[0]["vmid"] == 100
    assert snapshots[0]["vm_type"] == "qemu"

    # Check snapshot 2
    assert snapshots[1]["id"] == f"{cluster_id}:pve1/qemu/100:snapshot2"
    assert snapshots[1]["name"] == "snapshot2"


@patch.object(cartography.intel.proxmox.snapshot, "get_all_snapshots")
def test_snapshot_to_cluster_relationship(mock_get_snapshots, neo4j_session):
    """Test ProxmoxSnapshot RESOURCE relationship to ProxmoxCluster."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock snapshot data
    mock_snapshot_data = [
        {
            "name": "test-snap",
            "node": "pve1",
            "vmid": 100,
            "vm_type": "qemu",
            "description": "Test",
            "snaptime": 1704067200,
            "vmstate": 1,
            "parent": "",
        }
    ]
    mock_get_snapshots.return_value = mock_snapshot_data

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
        MOCK_VMS_FOR_SNAPSHOT,
    )

    # Assert - check relationship exists
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxSnapshot)-[:RESOURCE]->(c:ProxmoxCluster)
        WHERE c.id = $cluster_id
        RETURN s.name as snapshot_name, c.id as cluster_id
        """,
        cluster_id=cluster_id,
    )

    rels = list(result)
    assert len(rels) == 1
    assert rels[0]["snapshot_name"] == "test-snap"
    assert rels[0]["cluster_id"] == cluster_id


@patch.object(cartography.intel.proxmox.snapshot, "get_all_snapshots")
def test_snapshot_to_vm_relationship(mock_get_snapshots, neo4j_session):
    """Test ProxmoxSnapshot SNAPSHOT_OF relationship to ProxmoxVM."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Create a test VM
    neo4j_session.run(
        """
        MERGE (vm:ProxmoxVM {id: $vm_id})
        SET vm.vmid = $vmid,
            vm.cluster_id = $cluster_id,
            vm.name = 'test-vm',
            vm.type = 'qemu'
        """,
        vm_id=f"{cluster_id}:pve1/qemu/100",
        vmid=100,
        cluster_id=cluster_id,
    )

    # Mock snapshot data
    mock_snapshot_data = [
        {
            "name": "test-snap",
            "node": "pve1",
            "vmid": 100,
            "vm_type": "qemu",
            "description": "Test",
            "snaptime": 1704067200,
            "vmstate": 1,
            "parent": "",
        }
    ]
    mock_get_snapshots.return_value = mock_snapshot_data

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    # Act
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
        MOCK_VMS_FOR_SNAPSHOT,
    )

    # Assert - check relationship exists
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxSnapshot)-[:SNAPSHOT_OF]->(vm:ProxmoxVM)
        WHERE vm.vmid = $vmid AND vm.cluster_id = $cluster_id
        RETURN s.name as snapshot_name, vm.name as vm_name
        """,
        vmid=100,
        cluster_id=cluster_id,
    )

    rels = list(result)
    assert len(rels) == 1
    assert rels[0]["snapshot_name"] == "test-snap"
    assert rels[0]["vm_name"] == "test-vm"


@patch.object(cartography.intel.proxmox.snapshot, "get_all_snapshots")
def test_snapshot_multi_cluster_isolation(mock_get_snapshots, neo4j_session):
    """Test snapshots from different clusters don't merge."""
    # Setup two clusters
    cluster_a_id = create_test_cluster(neo4j_session, "cluster-a", TEST_UPDATE_TAG)
    cluster_b_id = create_test_cluster(neo4j_session, "cluster-b", TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Same snapshot name on both clusters
    mock_snapshot_data = [
        {
            "name": "daily-backup",
            "node": "pve1",
            "vmid": 100,
            "vm_type": "qemu",
            "description": "Daily backup",
            "snaptime": 1704067200,
            "vmstate": 1,
            "parent": "",
        }
    ]

    # Sync to cluster A
    mock_get_snapshots.return_value = mock_snapshot_data
    sync(
        neo4j_session,
        proxmox_client,
        cluster_a_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": cluster_a_id},
        MOCK_VMS_FOR_SNAPSHOT,
    )

    # Sync to cluster B
    mock_get_snapshots.return_value = mock_snapshot_data
    sync(
        neo4j_session,
        proxmox_client,
        cluster_b_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": cluster_b_id},
        MOCK_VMS_FOR_SNAPSHOT,
    )

    # Assert - should have 2 distinct snapshots
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxSnapshot)
        WHERE s.name = 'daily-backup'
        RETURN s.id as id, s.cluster_id as cluster_id
        ORDER BY s.id
        """
    )

    snapshots = list(result)
    assert len(snapshots) == 2

    # Different cluster IDs
    snapshot_ids = {s["id"] for s in snapshots}
    assert f"{cluster_a_id}:pve1/qemu/100:daily-backup" in snapshot_ids
    assert f"{cluster_b_id}:pve1/qemu/100:daily-backup" in snapshot_ids


@patch.object(cartography.intel.proxmox.snapshot, "get_all_snapshots")
def test_snapshot_cleanup_stale_data(mock_get_snapshots, neo4j_session):
    """Test cleanup removes stale snapshots from previous sync."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # First sync - create snapshot1 and snapshot2
    mock_snapshot_data = []
    for snapshot in MOCK_QEMU_SNAPSHOTS[:2]:  # Only first 2
        if snapshot["name"] != "current":
            snapshot_copy = snapshot.copy()
            snapshot_copy["node"] = "pve1"
            snapshot_copy["vmid"] = 100
            snapshot_copy["vm_type"] = "qemu"
            mock_snapshot_data.append(snapshot_copy)

    mock_get_snapshots.return_value = mock_snapshot_data

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
        MOCK_VMS_FOR_SNAPSHOT,
    )

    # Assert first sync created snapshots
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxSnapshot)
        WHERE s.cluster_id = $cluster_id
        RETURN count(s) as count
        """,
        cluster_id=cluster_id,
    )
    assert result.single()["count"] == 2

    # Second sync - only snapshot1 remains
    new_update_tag = TEST_UPDATE_TAG + 1
    mock_snapshot_data = [mock_snapshot_data[0]]  # Only first snapshot
    mock_get_snapshots.return_value = mock_snapshot_data

    common_job_parameters["UPDATE_TAG"] = new_update_tag

    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        new_update_tag,
        common_job_parameters,
        MOCK_VMS_FOR_SNAPSHOT,
    )

    # Assert stale snapshot2 was cleaned up
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxSnapshot)
        WHERE s.cluster_id = $cluster_id
        RETURN s.name as name
        """,
        cluster_id=cluster_id,
    )

    snapshots = list(result)
    assert len(snapshots) == 1
    assert snapshots[0]["name"] == "snapshot1"
