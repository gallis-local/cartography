"""
Integration tests for Proxmox firewall options sync.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.firewalloptions
from cartography.intel.proxmox.firewalloptions import sync
from tests.data.proxmox.firewalloptions import MOCK_CLUSTER_FIREWALL_OPTIONS
from tests.data.proxmox.firewalloptions import MOCK_NODE_FIREWALL_OPTIONS
from tests.integration.cartography.intel.proxmox import create_test_cluster


TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.firewalloptions, "get_cluster_firewall_options")
@patch.object(cartography.intel.proxmox.firewalloptions, "get_node_firewall_options")
def test_firewalloptions_sync(mock_get_node_options, mock_get_cluster_options, neo4j_session):
    """Test firewall options sync creates ProxmoxFirewallOptions nodes."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock firewall options data
    mock_get_cluster_options.return_value = MOCK_CLUSTER_FIREWALL_OPTIONS
    mock_get_node_options.return_value = MOCK_NODE_FIREWALL_OPTIONS

    # Mock node list
    proxmox_client.nodes.get.return_value = [{"node": "pve1"}]

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
    )

    # Assert - check options were created
    result = neo4j_session.run(
        """
        MATCH (o:ProxmoxFirewallOptions)
        WHERE o.cluster_id = $cluster_id
        RETURN o.id as id, o.scope as scope, o.scope_id as scope_id,
               o.policy_in as policy_in, o.policy_out as policy_out
        ORDER BY o.scope, o.scope_id
        """,
        cluster_id=cluster_id,
    )

    options = list(result)
    assert len(options) == 2

    # Check cluster-level options
    assert options[0]["id"] == f"{cluster_id}/firewall/options"
    assert options[0]["scope"] == "cluster"
    assert options[0]["scope_id"] is None
    assert options[0]["policy_in"] == "DROP"
    assert options[0]["policy_out"] == "ACCEPT"

    # Check node-level options
    assert options[1]["id"] == f"{cluster_id}/node/pve1/firewall/options"
    assert options[1]["scope"] == "node"
    assert options[1]["scope_id"] == "pve1"
    assert options[1]["policy_in"] == "ACCEPT"


@patch.object(cartography.intel.proxmox.firewalloptions, "get_cluster_firewall_options")
@patch.object(cartography.intel.proxmox.firewalloptions, "get_node_firewall_options")
def test_firewalloptions_to_cluster_relationship(
    mock_get_node_options, mock_get_cluster_options, neo4j_session
):
    """Test ProxmoxFirewallOptions RESOURCE relationship to ProxmoxCluster."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock firewall options data
    mock_get_cluster_options.return_value = MOCK_CLUSTER_FIREWALL_OPTIONS
    mock_get_node_options.return_value = {}

    proxmox_client.nodes.get.return_value = []

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
    )

    # Assert - check relationship exists
    result = neo4j_session.run(
        """
        MATCH (o:ProxmoxFirewallOptions)-[:RESOURCE]->(c:ProxmoxCluster)
        WHERE c.id = $cluster_id
        RETURN o.scope as scope, c.id as cluster_id
        """,
        cluster_id=cluster_id,
    )

    rels = list(result)
    assert len(rels) == 1
    assert rels[0]["scope"] == "cluster"
    assert rels[0]["cluster_id"] == cluster_id


@patch.object(cartography.intel.proxmox.firewalloptions, "get_cluster_firewall_options")
@patch.object(cartography.intel.proxmox.firewalloptions, "get_node_firewall_options")
def test_firewalloptions_multi_cluster_isolation(
    mock_get_node_options, mock_get_cluster_options, neo4j_session
):
    """Test firewall options from different clusters don't merge."""
    # Setup two clusters
    cluster_a_id = create_test_cluster(neo4j_session, "cluster-a", TEST_UPDATE_TAG)
    cluster_b_id = create_test_cluster(neo4j_session, "cluster-b", TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Same options on both clusters
    mock_get_cluster_options.return_value = MOCK_CLUSTER_FIREWALL_OPTIONS
    mock_get_node_options.return_value = {}
    proxmox_client.nodes.get.return_value = []

    # Sync to cluster A
    sync(
        neo4j_session,
        proxmox_client,
        cluster_a_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": cluster_a_id},
    )

    # Sync to cluster B
    sync(
        neo4j_session,
        proxmox_client,
        cluster_b_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": cluster_b_id},
    )

    # Assert - should have 2 distinct options
    result = neo4j_session.run(
        """
        MATCH (o:ProxmoxFirewallOptions)
        WHERE o.scope = 'cluster'
        RETURN o.id as id, o.cluster_id as cluster_id
        ORDER BY o.id
        """
    )

    options = list(result)
    assert len(options) == 2

    # Different cluster IDs
    option_ids = {o["id"] for o in options}
    assert f"{cluster_a_id}/firewall/options" in option_ids
    assert f"{cluster_b_id}/firewall/options" in option_ids


@patch.object(cartography.intel.proxmox.firewalloptions, "get_cluster_firewall_options")
@patch.object(cartography.intel.proxmox.firewalloptions, "get_node_firewall_options")
def test_firewalloptions_cleanup_stale_data(
    mock_get_node_options, mock_get_cluster_options, neo4j_session
):
    """Test cleanup removes stale firewall options from previous sync."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # First sync - create cluster and node options
    mock_get_cluster_options.return_value = MOCK_CLUSTER_FIREWALL_OPTIONS
    mock_get_node_options.return_value = MOCK_NODE_FIREWALL_OPTIONS
    proxmox_client.nodes.get.return_value = [{"node": "pve1"}, {"node": "pve2"}]

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
    )

    # Assert first sync created options
    result = neo4j_session.run(
        """
        MATCH (o:ProxmoxFirewallOptions)
        WHERE o.cluster_id = $cluster_id
        RETURN count(o) as count
        """,
        cluster_id=cluster_id,
    )
    assert result.single()["count"] == 3  # cluster + 2 nodes

    # Second sync - only cluster and one node remain
    new_update_tag = TEST_UPDATE_TAG + 1
    proxmox_client.nodes.get.return_value = [{"node": "pve1"}]

    common_job_parameters["UPDATE_TAG"] = new_update_tag

    sync(
        neo4j_session,
        proxmox_client,
        cluster_id,
        new_update_tag,
        common_job_parameters,
    )

    # Assert stale node options were cleaned up
    result = neo4j_session.run(
        """
        MATCH (o:ProxmoxFirewallOptions)
        WHERE o.cluster_id = $cluster_id
        RETURN o.scope as scope, o.scope_id as scope_id
        ORDER BY o.scope, o.scope_id
        """,
        cluster_id=cluster_id,
    )

    options = list(result)
    assert len(options) == 2
    assert options[0]["scope"] == "cluster"
    assert options[1]["scope"] == "node"
    assert options[1]["scope_id"] == "pve1"


@patch.object(cartography.intel.proxmox.firewalloptions, "get_cluster_firewall_options")
@patch.object(cartography.intel.proxmox.firewalloptions, "get_node_firewall_options")
def test_firewalloptions_enable_disable(
    mock_get_node_options, mock_get_cluster_options, neo4j_session
):
    """Test firewall options enable/disable status."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock firewall options with enable=1
    mock_get_cluster_options.return_value = MOCK_CLUSTER_FIREWALL_OPTIONS
    mock_get_node_options.return_value = {}
    proxmox_client.nodes.get.return_value = []

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
    )

    # Assert - check enabled status
    result = neo4j_session.run(
        """
        MATCH (o:ProxmoxFirewallOptions)
        WHERE o.cluster_id = $cluster_id
        RETURN o.enable as enable
        """,
        cluster_id=cluster_id,
    )

    options = result.single()
    assert options["enable"] is True


@patch.object(cartography.intel.proxmox.firewalloptions, "get_cluster_firewall_options")
@patch.object(cartography.intel.proxmox.firewalloptions, "get_node_firewall_options")
def test_firewalloptions_conntrack_settings(
    mock_get_node_options, mock_get_cluster_options, neo4j_session
):
    """Test firewall options connection tracking settings."""
    # Setup
    cluster_id = create_test_cluster(neo4j_session, TEST_CLUSTER_ID, TEST_UPDATE_TAG)
    proxmox_client = MagicMock()

    # Mock firewall options with conntrack settings
    mock_get_cluster_options.return_value = MOCK_CLUSTER_FIREWALL_OPTIONS
    mock_get_node_options.return_value = {}
    proxmox_client.nodes.get.return_value = []

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
    )

    # Assert - check conntrack settings
    result = neo4j_session.run(
        """
        MATCH (o:ProxmoxFirewallOptions)
        WHERE o.cluster_id = $cluster_id
        RETURN o.nf_conntrack_max as max,
               o.nf_conntrack_tcp_timeout_established as timeout
        """,
        cluster_id=cluster_id,
    )

    options = result.single()
    assert options["max"] == 262144
    assert options["timeout"] == 432000
