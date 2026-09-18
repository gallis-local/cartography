"""
OpenVAS TLS certificate ingestion.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.openvas.util import bool_or_none
from cartography.intel.openvas.util import int_or_none
from cartography.models.openvas.tls_certificates import (
    OpenVASCertificateToHostMatchLink,
)
from cartography.models.openvas.tls_certificates import OpenVASTLSCertificateSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _transform_tls_certificate(cert: Any) -> dict:
    """
    Transform a <tls_certificate> element from a get_tls_certificates response.

    Element names follow gvmd's get_tls_certificates_run(): subject_dn/issuer_dn
    (not subject/issuer), expiration_time (not not_after/expiry_time),
    sha256_fingerprint/md5_fingerprint (not fingerprint), and time_status (not
    status). The previous names matched no gvmd element, so every one of those
    properties -- including the certificate expiry date -- loaded as null.

    :param cert: A <tls_certificate> element
    :return: Node data dict for OpenVASTLSCertificateSchema
    """
    certificate = cert.find("certificate")

    return {
        "id": cert.get("id"),
        "name": cert.findtext("name"),
        "comment": cert.findtext("comment"),
        "creation_time": cert.findtext("creation_time"),
        "modification_time": cert.findtext("modification_time"),
        "subject_dn": cert.findtext("subject_dn"),
        "issuer_dn": cert.findtext("issuer_dn"),
        "serial": cert.findtext("serial"),
        "sha256_fingerprint": cert.findtext("sha256_fingerprint"),
        "md5_fingerprint": cert.findtext("md5_fingerprint"),
        "certificate_format": (
            certificate.get("format") if certificate is not None else None
        ),
        "activation_time": cert.findtext("activation_time"),
        "expiration_time": cert.findtext("expiration_time"),
        "last_seen": cert.findtext("last_seen"),
        "valid": bool_or_none(cert.findtext("valid")),
        "trust": int_or_none(cert.findtext("trust")),
        "time_status": cert.findtext("time_status"),
    }


def transform_tls_certificates(certs: list) -> tuple[list, list]:
    """
    Transform raw <tls_certificate> elements into (certificates, host links).

    :param certs: Raw <tls_certificate> elements
    :return: Tuple of (certificate node data, certificate-to-host link data)
    """
    cert_data = [_transform_tls_certificate(cert) for cert in certs]
    return cert_data, transform_certificate_host_links(certs)


def transform_certificate_host_links(certs: list) -> list:
    """
    Resolve which host IPs each certificate was observed on.

    With details requested, gvmd reports every observation of a certificate under
    <sources>, each carrying the host IP and the port it was served from. One
    certificate is routinely served on several ports of the same host (and the
    same port across hosts), so ports are aggregated into a list per
    (certificate, host) pair: a relationship keyed on its two endpoints would
    otherwise keep one port and silently drop the rest.

    :param certs: Raw <tls_certificate> elements
    :return: One dict per (certificate, host) pair with the observed ports
    """
    ports_by_pair: dict[tuple[str, str], list[str]] = {}
    for cert in certs:
        cert_id = cert.get("id")
        if not cert_id:
            continue
        for source in cert.findall("sources/source"):
            ip = source.findtext("location/host/ip")
            if not ip:
                continue
            ports = ports_by_pair.setdefault((cert_id, ip), [])
            port = source.findtext("location/port")
            if port and port not in ports:
                ports.append(port)
    return [
        {"certificate_id": cert_id, "host_ip": ip, "ports": ports or None}
        for (cert_id, ip), ports in ports_by_pair.items()
    ]


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
def load_certificate_host_links(
    neo4j_session: neo4j.Session,
    links: list,
    instance_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        OpenVASCertificateToHostMatchLink(),
        links,
        lastupdated=update_tag,
        _sub_resource_label="OpenVASInstance",
        _sub_resource_id=instance_id,
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
    GraphJob.from_matchlink(
        OpenVASCertificateToHostMatchLink(),
        "OpenVASInstance",
        common_job_parameters["OPENVAS_INSTANCE_ID"],
        common_job_parameters["UPDATE_TAG"],
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
    certs, host_links = transform_tls_certificates(raw_certs)
    load_tls_certificates(neo4j_session, certs, instance_id, update_tag)
    load_certificate_host_links(neo4j_session, host_links, instance_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
