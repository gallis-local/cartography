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


def link_cluster_resources(
    neo4j_session: neo4j.Session, cluster_id: str, update_tag: int
) -> None:
    """
    Attach every node carrying this cluster_id to the cluster with a RESOURCE edge.

    The real sync always produces ``(:ProxmoxCluster)-[:RESOURCE]->(node)`` because
    each node schema declares the cluster as its sub-resource. The typed analysis
    jobs scope themselves on that edge, so a test that only sets the ``cluster_id``
    property would silently match nothing.

    :param neo4j_session: Neo4j session
    :param cluster_id: Cluster ID whose resources should be attached
    :param update_tag: Update timestamp
    """
    neo4j_session.run(
        """
        MATCH (cluster:ProxmoxCluster {id: $cluster_id})
        MATCH (n {cluster_id: $cluster_id})
        WHERE n <> cluster
        MERGE (cluster)-[r:RESOURCE]->(n)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        """,
        cluster_id=cluster_id,
        update_tag=update_tag,
    )
