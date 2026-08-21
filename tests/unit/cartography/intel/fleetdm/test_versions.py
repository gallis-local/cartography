import cartography.intel.fleetdm.versions as versions
import tests.data.fleetdm.versions as test_data

TEST_UPDATE_TAG = 123456789


def test_transform_versions_and_vulnerabilities():
    version_data, vuln_data = versions.transform(
        test_data.MOCK_VERSIONS_RESPONSE,
        TEST_UPDATE_TAG,
    )

    assert len(version_data) == 3
    openssl = next(v for v in version_data if v["id"] == "3")
    assert openssl["vulnerabilities_count"] == 0

    assert len(vuln_data) == 2
    vuln_ids = {v["id"] for v in vuln_data}
    assert vuln_ids == {"1-CVE-2024-1234", "2-CVE-2024-5678"}

    # Each vulnerability must carry a software_version_id so it can be linked
    # back to the FleetDMSoftwareVersion node it was found on.
    for vuln in vuln_data:
        assert vuln["software_version_id"]
        matching_version_ids = {
            v["id"] for v in version_data if v["id"] == vuln["software_version_id"]
        }
        assert matching_version_ids == {vuln["software_version_id"]}


def test_transform_versions_no_vulnerabilities():
    raw = [
        {
            "id": 10,
            "name": "no-vuln-package",
            "version": "1.0.0",
            "source": "apps",
        }
    ]
    version_data, vuln_data = versions.transform(raw, TEST_UPDATE_TAG)

    assert len(version_data) == 1
    assert version_data[0]["vulnerabilities_count"] == 0
    assert vuln_data == []


def test_transform_versions_empty():
    version_data, vuln_data = versions.transform([], TEST_UPDATE_TAG)
    assert version_data == []
    assert vuln_data == []
