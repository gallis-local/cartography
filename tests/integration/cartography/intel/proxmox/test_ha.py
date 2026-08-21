"""
Integration tests for Proxmox HA sync.
"""

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.ha
from cartography.intel.proxmox.ha import sync
from tests.data.proxmox.ha import MOCK_HA_GROUP_DATA
from tests.data.proxmox.ha import MOCK_HA_RESOURCE_DATA
from tests.integration.cartography.intel.proxmox import create_test_cluster
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(
    cartography.intel.proxmox.ha, "get_ha_groups", return_value=MOCK_HA_GROUP_DATA
)
@patch.object(
    cartography.intel.proxmox.ha, "get_ha_resources", return_value=MOCK_HA_RESOURCE_DATA
)
def test_sync_ha(mock_get_resources, mock_get_groups, neo4j_session):
    """
    Test that HA groups and resources sync correctly.
    """
    # Arrange
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

    # Create VMs for relationship tests using new-style cluster-scoped IDs
    neo4j_session.run(
        """
        MERGE (v1:ProxmoxVM {id: 'test-cluster/vm/100'})
        SET v1.vmid = 100, v1.name = 'test-vm-1', v1.cluster_id = 'test-cluster',
            v1.lastupdated = $update_tag
        MERGE (v2:ProxmoxVM {id: 'test-cluster/vm/101'})
        SET v2.vmid = 101, v2.name = 'test-vm-2', v2.cluster_id = 'test-cluster',
            v2.lastupdated = $update_tag
        MERGE (v3:ProxmoxVM {id: 'test-cluster/vm/200'})
        SET v3.vmid = 200, v3.name = 'test-container-1', v3.cluster_id = 'test-cluster',
            v3.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.proxmox.ha.sync(
        neo4j_session,
        None,  # proxmox_client mocked
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - HA groups exist
    expected_groups = {
        ("test-cluster/ha/group/ha-group-1", "node1,node2"),
        ("test-cluster/ha/group/ha-group-2", "node2"),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxHAGroup", ["id", "nodes"]) == expected_groups
    )

    # Assert - HA resources exist
    expected_resources = {
        ("test-cluster/ha/resource/vm:100", "started"),
        ("test-cluster/ha/resource/ct:200", "started"),
        ("test-cluster/ha/resource/vm:101", "stopped"),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxHAResource", ["id", "state"])
        == expected_resources
    )

    # Assert - HA group to cluster relationships
    expected_group_rels = {
        ("test-cluster/ha/group/ha-group-1", TEST_CLUSTER_ID),
        ("test-cluster/ha/group/ha-group-2", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxHAGroup",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_group_rels
    )

    # Assert - HA resource to cluster relationships
    expected_resource_rels = {
        ("test-cluster/ha/resource/vm:100", TEST_CLUSTER_ID),
        ("test-cluster/ha/resource/ct:200", TEST_CLUSTER_ID),
        ("test-cluster/ha/resource/vm:101", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxHAResource",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_resource_rels
    )

    # Assert - HA resource to HA group relationships
    expected_ha_group_rels = {
        ("test-cluster/ha/resource/vm:100", "test-cluster/ha/group/ha-group-1"),
        ("test-cluster/ha/resource/ct:200", "test-cluster/ha/group/ha-group-1"),
        ("test-cluster/ha/resource/vm:101", "test-cluster/ha/group/ha-group-2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxHAResource",
            "id",
            "ProxmoxHAGroup",
            "id",
            "MEMBER_OF_HA_GROUP",
            rel_direction_right=True,
        )
        == expected_ha_group_rels
    )

    # Assert - HA resource to VM relationships
    result = neo4j_session.run(
        """
        MATCH (ha:ProxmoxHAResource)-[:PROTECTS]->(v:ProxmoxVM)
        RETURN ha.id as ha_id, v.vmid as vmid
        ORDER BY ha_id
        """
    )
    ha_vm_rels = [(r["ha_id"], r["vmid"]) for r in result]
    assert ha_vm_rels == [
        ("test-cluster/ha/resource/ct:200", 200),
        ("test-cluster/ha/resource/vm:100", 100),
        ("test-cluster/ha/resource/vm:101", 101),
    ]

    # Assert - HA group properties (Proxmox API returns 0/1, stored as integers in Neo4j)
    result = neo4j_session.run(
        """
        MATCH (g:ProxmoxHAGroup {id: 'test-cluster/ha/group/ha-group-2'})
        RETURN g.restricted as restricted, g.nofailback as nofailback
        """
    )
    record = result.single()
    assert record["restricted"] == 1  # Proxmox API returns 1 for true
    assert record["nofailback"] == 1  # Proxmox API returns 1 for true


@patch.object(
    cartography.intel.proxmox.ha, "get_ha_groups", return_value=MOCK_HA_GROUP_DATA
)
@patch.object(
    cartography.intel.proxmox.ha, "get_ha_resources", return_value=MOCK_HA_RESOURCE_DATA
)
def test_ha_cleanup_stale_data(mock_get_resources, mock_get_groups, neo4j_session):
    """
    Test that a second sync with fewer HA groups/resources removes the stale
    HAGroup/HAResource nodes and their MEMBER_OF_HA_GROUP/PROTECTS matchlinks.
    """
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Create VMs referenced by the PROTECTS matchlink
    neo4j_session.run(
        """
        MERGE (v1:ProxmoxVM {id: $cluster_id + '/vm/100'})
        SET v1.vmid = 100, v1.cluster_id = $cluster_id, v1.lastupdated = $update_tag
        MERGE (v2:ProxmoxVM {id: $cluster_id + '/vm/200'})
        SET v2.vmid = 200, v2.cluster_id = $cluster_id, v2.lastupdated = $update_tag
        MERGE (v3:ProxmoxVM {id: $cluster_id + '/vm/101'})
        SET v3.vmid = 101, v3.cluster_id = $cluster_id, v3.lastupdated = $update_tag
        """,
        cluster_id=cluster_id,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": cluster_id,
    }

    # First sync - full mock dataset (2 groups, 3 resources)
    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert len(check_nodes(neo4j_session, "ProxmoxHAGroup", ["id"])) == 2
    assert len(check_nodes(neo4j_session, "ProxmoxHAResource", ["id"])) == 3

    # Second sync - only one group and one resource remain
    new_update_tag = TEST_UPDATE_TAG + 1
    common_job_parameters["UPDATE_TAG"] = new_update_tag

    with (
        patch.object(
            cartography.intel.proxmox.ha,
            "get_ha_groups",
            return_value=[MOCK_HA_GROUP_DATA[0]],
        ),
        patch.object(
            cartography.intel.proxmox.ha,
            "get_ha_resources",
            return_value=[MOCK_HA_RESOURCE_DATA[0]],
        ),
    ):
        sync(
            neo4j_session,
            proxmox_client,
            cluster_id,
            new_update_tag,
            common_job_parameters,
        )

    # Assert stale HAGroup/HAResource nodes were removed
    assert check_nodes(neo4j_session, "ProxmoxHAGroup", ["id"]) == {
        ("test-cluster/ha/group/ha-group-1",),
    }
    assert check_nodes(neo4j_session, "ProxmoxHAResource", ["id"]) == {
        ("test-cluster/ha/resource/vm:100",),
    }

    # Assert stale MEMBER_OF_HA_GROUP / PROTECTS matchlinks were removed too
    result = neo4j_session.run(
        """
        MATCH (:ProxmoxHAResource)-[r:MEMBER_OF_HA_GROUP]->(:ProxmoxHAGroup)
        RETURN count(r) as count
        """
    )
    assert result.single()["count"] == 1

    result = neo4j_session.run(
        """
        MATCH (:ProxmoxHAResource)-[r:PROTECTS]->(:ProxmoxVM)
        RETURN count(r) as count
        """
    )
    assert result.single()["count"] == 1
