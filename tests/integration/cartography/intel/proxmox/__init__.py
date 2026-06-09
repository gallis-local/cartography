"""
Common utilities for Proxmox integration tests.
"""

import neo4j


def create_test_cluster(
    neo4j_session: neo4j.Session, cluster_id: str, update_tag: int
) -> str:
    """
    Create a test ProxmoxCluster node in Neo4j.

    :param neo4j_session: Neo4j session
    :param cluster_id: Cluster ID
    :param update_tag: Update timestamp
    :return: Cluster ID
    """
    neo4j_session.run(
        """
        MERGE (cluster:ProxmoxCluster {id: $cluster_id})
        ON CREATE SET cluster.firstseen = timestamp()
        SET cluster.lastupdated = $update_tag,
            cluster.name = $cluster_name
        """,
        cluster_id=cluster_id,
        cluster_name=f"Test Cluster {cluster_id}",
        update_tag=update_tag,
    )
    return cluster_id
