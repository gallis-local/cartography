"""
Integration tests for OpenVAS TLS certificate sync.
"""

import cartography.intel.openvas.hosts
import cartography.intel.openvas.tls_certificates
from tests.data.openvas.responses import CERT_ID_1
from tests.data.openvas.responses import CERT_ID_2
from tests.data.openvas.responses import HOST_ID_1
from tests.data.openvas.responses import INSTANCE_ID
from tests.integration.cartography.intel.openvas.util import common_job_parameters
from tests.integration.cartography.intel.openvas.util import FakeGmp
from tests.integration.cartography.intel.openvas.util import seed_instance
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_sync_tls_certificates(neo4j_session):
    """Certificates are loaded, labeled and linked to matching hosts."""
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
    cartography.intel.openvas.tls_certificates.sync_tls_certificates(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert
    cert_nodes = (
        check_nodes(
            neo4j_session,
            "OpenVASTLSCertificate",
            ["id", "name", "issuer", "not_after"],
        )
        or set()
    )
    assert (
        CERT_ID_1,
        "10.0.0.5",
        "CN=Example Root CA",
        "2025-01-01T00:00:00+00:00",
    ) in cert_nodes
    assert (
        CERT_ID_2,
        "10.0.0.99",
        "CN=Example Root CA",
        "2025-06-01T00:00:00+00:00",
    ) in cert_nodes

    # Certificates carry the CERTIFICATE semantic label.
    labeled = check_nodes(neo4j_session, "Certificate", ["id"]) or set()
    assert (CERT_ID_1,) in labeled

    # CERT_ID_1 matches host ip 10.0.0.5; CERT_ID_2 matches no host.
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
    assert (CERT_ID_1, HOST_ID_1) in rels
    assert (CERT_ID_2, HOST_ID_1) not in rels


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

    # Act
    cartography.intel.openvas.tls_certificates.sync_tls_certificates(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )
    # CERT_ID_1 no longer matches any host on the second sync.
    changed_gmp = FakeGmp()
    changed_gmp._responses["get_tls_certificates"] = changed_gmp._responses[
        "get_tls_certificates"
    ].replace("<name>10.0.0.5</name>", "<name>10.0.0.99</name>", 1)
    cartography.intel.openvas.tls_certificates.sync_tls_certificates(
        neo4j_session,
        changed_gmp,
        INSTANCE_ID,
        TEST_UPDATE_TAG_2,
        {**common_job_parameters(), "UPDATE_TAG": TEST_UPDATE_TAG_2},
    )

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
    assert (CERT_ID_1, HOST_ID_1) not in rels
