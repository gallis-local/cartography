"""
Proxmox authentication realm sync module.

Syncs authentication realms (PAM, LDAP, AD, etc.).
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.proxmox.authrealm import ProxmoxAuthRealmSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_auth_realms(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get all authentication realms in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of auth realm dicts
    """
    try:
        return proxmox_client.access.domains.get()
    except Exception as e:
        logger.debug(f"Could not fetch authentication realms: {e}")
        return []


def transform_auth_realm_data(
    realms: list[dict[str, Any]],
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform auth realm data into standard format.

    :param realms: Raw auth realm data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed auth realm dicts
    """
    transformed_realms = []

    for realm in realms:
        # Required fields
        realm_name = realm["realm"]
        realm_id = f"{cluster_id}/realm/{realm_name}"

        transformed_realms.append(
            {
                "id": realm_id,
                "realm": realm_name,
                "cluster_id": cluster_id,
                "type": realm.get("type"),  # pam, ldap, ad, pve, openid
                "comment": realm.get("comment"),
                "default": realm.get("default", 0) == 1,  # Convert to boolean
                "tfa": realm.get("tfa"),  # Two-factor auth type
            }
        )

    return transformed_realms


def load_auth_realms(
    neo4j_session: neo4j.Session,
    realms: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load auth realm data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param realms: List of transformed auth realm dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxAuthRealmSchema(),
        realms,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync authentication realms.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Proxmox cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters for GraphJob
    """
    logger.info("Syncing Proxmox authentication realms")

    raw_realms = get_auth_realms(proxmox_client)

    transformed_realms = transform_auth_realm_data(raw_realms, cluster_id)

    load_auth_realms(neo4j_session, transformed_realms, cluster_id, update_tag)

    logger.info(f"Synced {len(transformed_realms)} authentication realms")

    cleanup(neo4j_session, common_job_parameters)

def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    """
    Remove stale auth realm data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    """
    GraphJob.from_node_schema(ProxmoxAuthRealmSchema(), common_job_parameters).run(
        neo4j_session
    )
