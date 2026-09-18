from cartography.intel.openvas.tls_certificates import transform_certificate_host_links
from cartography.intel.openvas.tls_certificates import transform_tls_certificates
from tests.data.openvas.responses import CERT_ID_1
from tests.data.openvas.responses import CERT_ID_2
from tests.data.openvas.responses import GET_TLS_CERTIFICATES_RESPONSE
from tests.data.openvas.responses import parse


def _certs() -> list:
    return parse(GET_TLS_CERTIFICATES_RESPONSE).findall("tls_certificate")


def test_transform_uses_gvmd_element_names():
    # subject_dn/issuer_dn/expiration_time/sha256_fingerprint/time_status are
    # the names gvmd actually emits; the older subject/issuer/not_after/
    # fingerprint/status names matched nothing and loaded as null.
    cert = transform_tls_certificates(_certs())[0][0]

    assert cert["id"] == CERT_ID_1
    assert cert["subject_dn"] == "CN=web-01.example.com"
    assert cert["issuer_dn"] == "CN=Example Root CA"
    assert cert["expiration_time"] == "2025-01-01T00:00:00+00:00"
    assert cert["sha256_fingerprint"] == "AABBCC1122334455"
    assert cert["time_status"] == "valid"
    assert cert["certificate_format"] == "DER"
    assert cert["last_seen"] == "2024-06-01T12:00:00+00:00"


def test_transform_coerces_valid_and_trust():
    certs, _ = transform_tls_certificates(_certs())
    valid_cert, expired_cert = certs

    assert valid_cert["valid"] is True
    assert valid_cert["trust"] == 1
    assert expired_cert["valid"] is False
    assert expired_cert["trust"] is None


def test_host_links_aggregate_ports_per_pair():
    # Two <source> entries for the same host differ only by port. Keying an edge
    # on its endpoints alone would keep one port and drop the other.
    links = transform_certificate_host_links(_certs())

    by_ip = {link["host_ip"]: link for link in links}
    assert set(by_ip) == {"10.0.0.5", "10.0.0.6"}
    assert by_ip["10.0.0.5"]["ports"] == ["443", "8443"]
    assert by_ip["10.0.0.6"]["ports"] == ["443"]
    assert {link["certificate_id"] for link in links} == {CERT_ID_1}


def test_host_links_skip_certificates_with_no_sources():
    links = transform_certificate_host_links(_certs())

    assert CERT_ID_2 not in {link["certificate_id"] for link in links}
