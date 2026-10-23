import pytest

from cartography.intel.harbor import sbom
from cartography.intel.harbor import vulnerabilities
from cartography.intel.harbor.util import encode_repository_name
from cartography.intel.harbor.util import normalize_base_url
from cartography.intel.harbor.util import pick_report
from tests.data.harbor import api

IMAGE = {"id": "h/p/r@sha256:a", "digest": "sha256:a"}


def test_normalize_base_url_lowercases_host_and_drops_trailing_slash():
    assert normalize_base_url(" https://Harbor.Example.com:8443/ ") == (
        "https://harbor.example.com:8443",
        "harbor.example.com:8443",
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://harbor.example.com",
        "harbor.example.com",
        "https://harbor.example.com/api/v2.0",
        "https://harbor.example.com?x=1",
    ],
)
def test_normalize_base_url_rejects_unsafe_or_ambiguous_urls(url):
    with pytest.raises(ValueError):
        normalize_base_url(url)


def test_repository_names_are_double_encoded():
    assert encode_repository_name("app/api") == "app%252Fapi"
    assert encode_repository_name("nginx") == "nginx"


def test_pick_report_matches_any_version_suffix():
    report = {"vulnerabilities": []}
    payload = {"application/vnd.security.vulnerability.report; version=1.1": report}
    assert (
        pick_report(payload, "application/vnd.security.vulnerability.report") is report
    )
    assert pick_report({"other": report}, "application/vnd.security") is None


def test_vulnerability_transform_handles_missing_optional_fields():
    findings = vulnerabilities.transform(api.NGINX_VULNERABILITIES, IMAGE)
    by_id = {f["vulnerability_id"]: f for f in findings}

    ghsa = by_id["GHSA-xxxx-yyyy-zzzz"]
    assert ghsa["cve_id"] is None
    assert ghsa["has_cve"] == "false"
    assert ghsa["fix_version"] is None
    assert ghsa["links"] == []
    assert ghsa["cvss_v3_score"] is None

    cve = by_id["CVE-2024-0001"]
    assert cve["has_cve"] == "true"
    assert cve["severity"] == "HIGH"
    assert cve["cvss_v2_vector"] is None
    assert cve["package_node_id"] == "h/p/r@sha256:a|openssl|3.0.2"


def test_vulnerability_transform_deduplicates_repeated_findings():
    item = api.NGINX_VULNERABILITIES[api.VULN_MIME]["vulnerabilities"][0]
    report = {api.VULN_MIME: {"vulnerabilities": [item, item]}}
    assert len(vulnerabilities.transform(report, IMAGE)) == 1


def test_vulnerability_transform_returns_nothing_without_a_report():
    assert vulnerabilities.transform({}, IMAGE) == []
    assert (
        vulnerabilities.transform({api.VULN_MIME: {"vulnerabilities": None}}, IMAGE)
        == []
    )


def test_sbom_transform_skips_the_image_root_and_missing_licenses():
    packages = sbom.transform(api.NGINX_SBOM, IMAGE)
    assert {p["name"] for p in packages} == {"openssl", "libfoo"}
    libfoo = next(p for p in packages if p["name"] == "libfoo")
    assert libfoo["license"] is None
    assert libfoo["purl"] is None


@pytest.mark.parametrize(
    "wrapper",
    [
        lambda doc: doc,
        lambda doc: {"sbom": doc},
        lambda doc: {"application/spdx+json": doc},
        lambda doc: {"application/spdx+json": {"sbom": doc}},
    ],
)
def test_sbom_transform_accepts_bare_and_wrapped_documents(wrapper):
    assert len(sbom.transform(wrapper(api.NGINX_SBOM), IMAGE)) == 2


def test_sbom_transform_fails_loudly_on_an_unknown_payload():
    with pytest.raises(ValueError):
        sbom.transform({"unexpected": "shape"}, IMAGE)
