"""
OpenVAS TLS certificate ingestion.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.models.openvas.tls_certificates import OpenVASTLSCertificateSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _transform_tls_certificate(cert: Any) -> dict:
    return {
        "id": cert.get("id"),
        "name": cert.findtext("name"),
        "subject": cert.findtext("subject"),
        "issuer": cert.findtext("issuer"),
        "not_before": cert.findtext("not_before"),
        "not_after": cert.findtext("not_after"),
        "serial": cert.findtext("serial"),
        "fingerprint": cert.findtext("fingerprint"),
        "certificate_format": cert.findtext("certificate_format"),
        "key_type": cert.findtext("key_type"),
        "key_bits": cert.findtext("key_bits"),
        "activation_time": cert.findtext("activation_time"),
        "expiry_time": cert.findtext("expiry_time"),
        "source_type": cert.findtext("source_type"),
        "status": cert.findtext("status"),
    }


def transform_tls_certificates(certs: list) -> list:
    return [_transform_tls_certificate(cert) for cert in certs]


@timeit
def load_tls_certificates(
    neo4j_session: neo4j.Session,
    certs: list,
    instance_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OpenVASTLSCertificateSchema(),
        certs,
        lastupdated=update_tag,
        OPENVAS_INSTANCE_ID=instance_id,
    )


@timeit
def _link_certificates_to_hosts(
    neo4j_session: neo4j.Session,
    instance_id: str,
    update_tag: int,
) -> None:
    """
    Link TLS certificates to the OpenVAS hosts that presented them.

    GMP does not expose which host a certificate was observed on, so the link
    is made by fuzzy-matching the certificate name against host ips/hostnames.
    """
    run_write_query(
        neo4j_session,
        """
        MATCH (cert:OpenVASTLSCertificate {instance_id: $INSTANCE_ID})
        MATCH (host:OpenVASHost {instance_id: $INSTANCE_ID})
        WHERE cert.name = host.ip OR cert.name = host.hostname
        MERGE (cert)-[r:CERTIFICATE_FOR]->(host)
        SET r.lastupdated = $UPDATE_TAG
        """,
        INSTANCE_ID=instance_id,
        UPDATE_TAG=update_tag,
    )
    # Clean up stale links from certificates that no longer match a host.
    run_write_query(
        neo4j_session,
        """
        MATCH (cert:OpenVASTLSCertificate {instance_id: $INSTANCE_ID})
            -[r:CERTIFICATE_FOR]->(host:OpenVASHost {instance_id: $INSTANCE_ID})
        WHERE r.lastupdated <> $UPDATE_TAG
        DELETE r
        """,
        INSTANCE_ID=instance_id,
        UPDATE_TAG=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running OpenVAS TLS certificate cleanup job")
    GraphJob.from_node_schema(
        OpenVASTLSCertificateSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_tls_certificates(
    neo4j_session: neo4j.Session,
    gmp: Any,
    instance_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync OpenVAS TLS certificates into the graph.
    """
    logger.info("Syncing OpenVAS TLS certificates")
    from cartography.intel.openvas import api

    raw_certs = api.get_tls_certificates(gmp)
    certs = transform_tls_certificates(raw_certs)
    load_tls_certificates(neo4j_session, certs, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    _link_certificates_to_hosts(neo4j_session, instance_id, update_tag)
