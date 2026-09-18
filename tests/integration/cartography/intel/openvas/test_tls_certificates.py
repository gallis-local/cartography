"""
Integration tests for OpenVAS TLS certificate sync.
"""

import cartography.intel.openvas.hosts
import cartography.intel.openvas.tls_certificates
from tests.data.openvas.responses import CERT_ID_1
from tests.data.openvas.responses import CERT_ID_2
from tests.data.openvas.responses import INSTANCE_ID
from tests.integration.cartography.intel.openvas.util import common_job_parameters
from tests.integration.cartography.intel.openvas.util import FakeGmp
from tests.integration.cartography.intel.openvas.util import seed_instance
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _sync(neo4j_session, gmp=None, update_tag=TEST_UPDATE_TAG):
    cartography.intel.openvas.tls_certificates.sync_tls_certificates(
        neo4j_session,
        gmp or FakeGmp(),
        INSTANCE_ID,
        update_tag,
        {**common_job_parameters(), "UPDATE_TAG": update_tag},
    )


def test_sync_tls_certificates(neo4j_session):
    """Certificates are loaded, labeled and linked to their observed hosts."""
    # Arrange
    seed_instance(neo4j_session)
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Act
    _sync(neo4j_session)

    # Assert
    cert_nodes = (
        check_nodes(
            neo4j_session,
            "OpenVASTLSCertificate",
            ["id", "issuer_dn", "expiration_time", "time_status"],
        )
        or set()
    )
    assert (
        CERT_ID_1,
        "CN=Example Root CA",
        "2025-01-01T00:00:00+00:00",
        "valid",
    ) in cert_nodes
    assert (
        CERT_ID_2,
        "CN=Example Root CA",
        "2025-06-01T00:00:00+00:00",
        "expired",
    ) in cert_nodes

    # Certificates carry the CERTIFICATE semantic label.
    labeled = check_nodes(neo4j_session, "Certificate", ["id"]) or set()
    assert (CERT_ID_1,) in labeled

    # CERT_ID_1 was observed on both fixture hosts; CERT_ID_2 has no sources.
    rels = (
        check_rels(
            neo4j_session,
            "OpenVASTLSCertificate",
            "id",
            "OpenVASHost",
            "id",
            "CERTIFICATE_FOR",
            rel_direction_right=True,
        )
        or set()
    )
    assert rels == {(CERT_ID_1, "10.0.0.5"), (CERT_ID_1, "10.0.0.6")}


def test_certificate_host_link_keeps_every_observed_port(neo4j_session):
    """Two observations of one certificate on one host keep both ports."""
    # Arrange
    seed_instance(neo4j_session)
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Act
    _sync(neo4j_session)

    # Assert
    ports = neo4j_session.run(
        """
        MATCH (:OpenVASTLSCertificate {id: $cert_id})-[r:CERTIFICATE_FOR]->
              (:OpenVASHost {id: '10.0.0.5'})
        RETURN r.ports AS ports
        """,
        cert_id=CERT_ID_1,
    ).single()["ports"]
    assert sorted(ports) == ["443", "8443"]


def test_sync_tls_certificates_cleans_stale_links(neo4j_session):
    """CERTIFICATE_FOR edges are refreshed and stale ones removed."""
    # Arrange
    seed_instance(neo4j_session)
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )
    _sync(neo4j_session)

    # Act: the certificate is no longer observed on 10.0.0.6.
    changed_gmp = FakeGmp()
    changed_gmp._responses["get_tls_certificates"] = changed_gmp._responses[
        "get_tls_certificates"
    ].replace("<ip>10.0.0.6</ip>", "<ip>10.0.0.99</ip>", 1)
    _sync(neo4j_session, changed_gmp, TEST_UPDATE_TAG_2)

    # Assert
    rels = (
        check_rels(
            neo4j_session,
            "OpenVASTLSCertificate",
            "id",
            "OpenVASHost",
            "id",
            "CERTIFICATE_FOR",
            rel_direction_right=True,
        )
        or set()
    )
    assert rels == {(CERT_ID_1, "10.0.0.5")}
