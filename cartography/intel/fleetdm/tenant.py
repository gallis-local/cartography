import logging

import neo4j

from cartography.client.core.tx import load
from cartography.models.fleetdm.tenant import FleetDMTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_tenant(
    neo4j_session: neo4j.Session,
    base_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FleetDMTenantSchema(),
        [{"id": base_url, "base_url": base_url, "name": base_url}],
        lastupdated=update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    base_url: str,
    update_tag: int,
) -> None:
    load_tenant(neo4j_session, base_url, update_tag)
