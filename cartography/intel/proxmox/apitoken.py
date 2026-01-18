"""
Proxmox API token sync module.

Syncs API tokens for user authentication.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.proxmox.apitoken import ProxmoxAPITokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


def get_tokens_for_user(
    proxmox_client: Any,
    userid: str,
) -> List[Dict[str, Any]]:
    """
    Get API tokens for a specific user.

    :param proxmox_client: Proxmox API client
    :param userid: User ID (format: user@realm)
    :return: List of token dicts
    """
    try:
        return proxmox_client.access.users(userid).token.get()
    except Exception as e:
        logger.debug(f"Could not fetch tokens for user {userid}: {e}")
        return []


def get_all_tokens(
    proxmox_client: Any,
    users: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Get all API tokens across all users.

    :param proxmox_client: Proxmox API client
    :param users: List of user dicts (must have 'userid' field)
    :return: List of token dicts with user metadata
    """
    all_tokens = []

    for user in users:
        userid = user.get("userid")
        if not userid:
            logger.warning(f"Skipping user with missing userid: {user}")
            continue

        tokens = get_tokens_for_user(proxmox_client, userid)

        # Add user metadata to each token
        for token in tokens:
            token["userid"] = userid

        all_tokens.extend(tokens)

    return all_tokens


# ============================================================================
# TRANSFORM functions
# ============================================================================


def transform_token_data(
    tokens: List[Dict[str, Any]],
    cluster_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform API token data into standard format.

    :param tokens: Raw token data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed token dicts
    """
    transformed_tokens = []

    for token in tokens:
        # Required fields
        tokenid = token["tokenid"]
        userid = token["userid"]

        # Create unique ID: cluster:userid!tokenid
        token_id = f"{cluster_id}:{userid}!{tokenid}"

        transformed_tokens.append(
            {
                "id": token_id,
                "tokenid": tokenid,
                "cluster_id": cluster_id,
                "userid": userid,
                "expire": token.get("expire", 0),  # 0 = never expires
                "privsep": token.get("privsep", 1) == 1,  # Convert to boolean
                "comment": token.get("comment"),
            }
        )

    return transformed_tokens


# ============================================================================
# LOAD functions
# ============================================================================


def load_tokens(
    neo4j_session: neo4j.Session,
    tokens: List[Dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load API token data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param tokens: List of transformed token dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxAPITokenSchema(),
        tokens,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


# ============================================================================
# SYNC function
# ============================================================================


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
    users: List[Dict[str, Any]],
) -> None:
    """
    Sync API tokens for all users.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Proxmox cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters for GraphJob
    :param users: List of users to fetch tokens for
    """
    logger.info("Syncing Proxmox API tokens")

    # GET - retrieve data from API
    raw_tokens = get_all_tokens(proxmox_client, users)

    # TRANSFORM - convert to standard format
    transformed_tokens = transform_token_data(raw_tokens, cluster_id)

    # LOAD - ingest to Neo4j
    load_tokens(neo4j_session, transformed_tokens, cluster_id, update_tag)

    # CLEANUP - remove stale tokens
    cleanup(neo4j_session, common_job_parameters)

    logger.info(f"Synced {len(transformed_tokens)} API tokens")


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Remove stale API token data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    """
    GraphJob.from_node_schema(ProxmoxAPITokenSchema(), common_job_parameters).run(
        neo4j_session
    )
