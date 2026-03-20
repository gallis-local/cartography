"""
Integration tests for Proxmox pool sync.
"""

from typing import Any
from unittest.mock import patch

import cartography.intel.proxmox.pool
from tests.data.proxmox.pool import MOCK_POOL_DATA
from tests.data.proxmox.pool import MOCK_POOL_DETAILS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.pool, "get_pools", return_value=MOCK_POOL_DATA)
@patch.object(cartography.intel.proxmox.pool, "get_pool_details")
def test_sync_pools(mock_get_pool_details, mock_get_pools, neo4j_session):
    """
    Test that pools sync correctly and create proper nodes and relationships.
    """

    # Arrange
    def get_details_side_effect(proxmox_client, poolid):
        return MOCK_POOL_DETAILS.get(poolid, {})

    mock_get_pool_details.side_effect = get_details_side_effect

    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Create cluster first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id,
            c.lastupdated = $update_tag
        """,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create VMs and storage for relationship tests
    neo4j_session.run(
        """
        MERGE (v1:ProxmoxVM {vmid: 100})
        SET v1.id = 'test-cluster/vm/100',
            v1.name = 'test-vm-1',
            v1.cluster_id = 'test-cluster',
            v1.lastupdated = $update_tag
        MERGE (v2:ProxmoxVM {vmid: 101})
        SET v2.id = 'test-cluster/vm/101',
            v2.name = 'test-vm-2',
            v2.cluster_id = 'test-cluster',
            v2.lastupdated = $update_tag
        MERGE (v3:ProxmoxVM {vmid: 200})
        SET v3.id = 'test-cluster/vm/200',
            v3.name = 'test-container-1',
            v3.cluster_id = 'test-cluster',
            v3.lastupdated = $update_tag
        MERGE (s:ProxmoxStorage {id: 'test-cluster/storage/nfs-backup'})
        SET s.name = 'nfs-backup',
            s.cluster_id = 'test-cluster',
            s.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.proxmox.pool.sync(
        neo4j_session,
        None,  # proxmox_client mocked
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Pools exist
    expected_pools = {
        ("test-cluster/pool/production", "Production VMs and containers"),
        ("test-cluster/pool/development", "Development environment"),
        ("test-cluster/pool/backup-storage", "Backup storage resources"),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxPool", ["id", "comment"]) == expected_pools
    )

    # Assert - Pool to cluster relationships
    expected_rels = {
        ("test-cluster/pool/production", TEST_CLUSTER_ID),
        ("test-cluster/pool/development", TEST_CLUSTER_ID),
        ("test-cluster/pool/backup-storage", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxPool",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert - Pool to VM relationships
    result = neo4j_session.run(
        """
        MATCH (p:ProxmoxPool)-[:CONTAINS_VM]->(v:ProxmoxVM)
        RETURN p.id as pool_id, v.vmid as vmid
        ORDER BY pool_id, vmid
        """
    )
    pool_vm_rels = [(r["pool_id"], r["vmid"]) for r in result]
    assert pool_vm_rels == [
        ("test-cluster/pool/development", 101),
        ("test-cluster/pool/production", 100),
        ("test-cluster/pool/production", 200),
    ]

    # Assert - Pool to storage relationships
    result = neo4j_session.run(
        """
        MATCH (p:ProxmoxPool)-[:CONTAINS_STORAGE]->(s:ProxmoxStorage)
        RETURN p.id as pool_id, s.id as storage_id
        """
    )
    pool_storage_rels = [(r["pool_id"], r["storage_id"]) for r in result]
    assert pool_storage_rels == [("test-cluster/pool/backup-storage", "test-cluster/storage/nfs-backup")]
