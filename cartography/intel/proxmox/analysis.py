"""
Post-ingestion analysis for Proxmox: creates derived graph relationships.

These functions run after all data has been loaded and create higher-level
relationships that make security queries easier (e.g. HAS_PERMISSION).
"""

import logging

import neo4j

from cartography.client.core.tx import run_write_query

logger = logging.getLogger(__name__)


def run_effective_permissions(
    neo4j_session: neo4j.Session,
    update_tag: int,
    cluster_id: str,
) -> None:
    """
    Create derived relationships showing effective permissions.

    This creates direct HAS_PERMISSION relationships from users/groups to resources,
    making it easier to query "what can this user access?" or "who can access this VM?"

    :param neo4j_session: Neo4j session
    :param update_tag: Sync timestamp
    :param cluster_id: Cluster ID to scope cleanup (prevents cross-cluster edge deletion)
    """
    logger.info(
        "Running Proxmox effective permissions analysis for cluster %s", cluster_id
    )

    # Create direct user -> resource permissions (through ACLs)
    query = """
    MATCH (u:ProxmoxUser)<-[:APPLIES_TO_USER]-(acl:ProxmoxACL)-[:GRANTS_ROLE]->(role:ProxmoxRole)
    MATCH (acl)-[:GRANTS_ACCESS_TO]->(resource)
    WHERE resource:ProxmoxVM OR resource:ProxmoxStorage OR resource:ProxmoxPool OR
          resource:ProxmoxNode OR resource:ProxmoxCluster
    WITH u, resource, role, acl
    MERGE (u)-[r:HAS_PERMISSION]->(resource)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag,
        r.via_acl = acl.id,
        r.role = role.roleid,
        r.privileges = role.privs,
        r.path = acl.path,
        r.propagate = acl.propagate
    """
    run_write_query(neo4j_session, query, UpdateTag=update_tag)

    # Create group -> resource permissions
    query = """
    MATCH (g:ProxmoxGroup)<-[:APPLIES_TO_GROUP]-(acl:ProxmoxACL)-[:GRANTS_ROLE]->(role:ProxmoxRole)
    MATCH (acl)-[:GRANTS_ACCESS_TO]->(resource)
    WHERE resource:ProxmoxVM OR resource:ProxmoxStorage OR resource:ProxmoxPool OR
          resource:ProxmoxNode OR resource:ProxmoxCluster
    WITH g, resource, role, acl
    MERGE (g)-[r:HAS_PERMISSION]->(resource)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag,
        r.via_acl = acl.id,
        r.role = role.roleid,
        r.privileges = role.privs,
        r.path = acl.path,
        r.propagate = acl.propagate
    """
    run_write_query(neo4j_session, query, UpdateTag=update_tag)

    # Create inherited permissions: user -> group -> resource
    query = """
    MATCH (u:ProxmoxUser)-[:MEMBER_OF]->(g:ProxmoxGroup)-[gp:HAS_PERMISSION]->(resource)
    WHERE resource:ProxmoxVM OR resource:ProxmoxStorage OR resource:ProxmoxPool OR
          resource:ProxmoxNode OR resource:ProxmoxCluster
    WITH u, resource, gp
    MERGE (u)-[r:HAS_PERMISSION]->(resource)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag,
        r.via_acl = gp.via_acl,
        r.via_group = true,
        r.role = gp.role,
        r.privileges = gp.privileges,
        r.path = gp.path,
        r.propagate = gp.propagate
    """
    run_write_query(neo4j_session, query, UpdateTag=update_tag)

    # Clean up stale HAS_PERMISSION relationships for this cluster only.
    # Scoped to users/groups belonging to this cluster to avoid clobbering
    # HAS_PERMISSION edges that belong to other clusters in a multi-cluster setup.
    cleanup_query = """
    MATCH (:ProxmoxUser {cluster_id: $ClusterId})-[r:HAS_PERMISSION]->()
    WHERE r.lastupdated < $UpdateTag
    DELETE r
    UNION
    MATCH (:ProxmoxGroup {cluster_id: $ClusterId})-[r:HAS_PERMISSION]->()
    WHERE r.lastupdated < $UpdateTag
    DELETE r
    """
    run_write_query(
        neo4j_session, cleanup_query, UpdateTag=update_tag, ClusterId=cluster_id
    )


def run_has_role_relationships(
    neo4j_session: neo4j.Session,
    update_tag: int,
    cluster_id: str,
) -> None:
    """
    Create direct HAS_ROLE relationships from users to roles.

    By default, ProxmoxUser-to-Role connections go through an intermediate
    ProxmoxACL node. This analysis materializes a direct (:ProxmoxUser)
    -[:HAS_ROLE]->(:ProxmoxRole) edge for the ontology.

    :param neo4j_session: Neo4j session
    :param update_tag: Sync timestamp
    :param cluster_id: Cluster ID to scope cleanup
    """
    logger.info("Running Proxmox HAS_ROLE analysis for cluster %s", cluster_id)

    query = """
    MATCH (u:ProxmoxUser {cluster_id: $ClusterId})
        <-[:APPLIES_TO_USER]-(acl:ProxmoxACL)-[:GRANTS_ROLE]->(role:ProxmoxRole)
    WITH DISTINCT u, role, acl.path AS acl_path, acl.propagate AS acl_propagate
    MERGE (u)-[r:HAS_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag,
        r.path = acl_path,
        r.propagate = acl_propagate
    """
    run_write_query(neo4j_session, query, UpdateTag=update_tag, ClusterId=cluster_id)

    # Clean up stale HAS_ROLE relationships for this cluster
    cleanup_query = """
    MATCH (:ProxmoxUser {cluster_id: $ClusterId})-[r:HAS_ROLE]->()
    WHERE r.lastupdated < $UpdateTag
    DELETE r
    """
    run_write_query(
        neo4j_session, cleanup_query, UpdateTag=update_tag, ClusterId=cluster_id
    )
