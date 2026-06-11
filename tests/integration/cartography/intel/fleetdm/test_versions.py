from unittest.mock import patch

import neo4j
import requests

import cartography.intel.fleetdm.tenant
import cartography.intel.fleetdm.versions
import tests.data.fleetdm.versions
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "https://fleet.example.com"


def _create_tenant(neo4j_session: neo4j.Session) -> None:
    cartography.intel.fleetdm.tenant.load_tenant(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.fleetdm.versions,
    "get",
    return_value=tests.data.fleetdm.versions.MOCK_VERSIONS_RESPONSE,
)
def test_sync_fleetdm_versions_and_vulnerabilities(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first (sub_resource_relationship uses OPTIONAL MATCH)
    _create_tenant(neo4j_session)

    # Act
    cartography.intel.fleetdm.versions.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Tenant exists
    expected_tenants = {(TEST_TENANT_ID,)}
    assert (
        check_nodes(
            neo4j_session,
            "FleetDMTenant",
            ["id"],
        )
        == expected_tenants
    )

    # Assert Software Versions exist
    expected_versions = {
        ("1", "1password", "8.10.36", "apps"),
        ("2", "chromium", "124.0.6367.60", "deb_packages"),
        ("3", "openssl", "3.0.12", "deb_packages"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "FleetDMSoftwareVersion",
            ["id", "name", "version", "source"],
        )
        == expected_versions
    )

    # Assert Software Versions connected to Tenant via RESOURCE
    expected_version_rels = {
        ("1", TEST_TENANT_ID),
        ("2", TEST_TENANT_ID),
        ("3", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "FleetDMSoftwareVersion",
            "id",
            "FleetDMTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_version_rels
    )

    # Assert Vulnerabilities exist
    expected_vulns = {
        ("1-CVE-2024-1234", "CVE-2024-1234", 7.5, True),
        ("2-CVE-2024-5678", "CVE-2024-5678", 8.2, False),
    }
    assert (
        check_nodes(
            neo4j_session,
            "FleetDMVulnerability",
            ["id", "cve_id", "cvss_score", "cisa_known_exploit"],
        )
        == expected_vulns
    )

    # Assert Vulnerabilities connected to Tenant via RESOURCE
    expected_vuln_rels = {
        ("1-CVE-2024-1234", TEST_TENANT_ID),
        ("2-CVE-2024-5678", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "FleetDMVulnerability",
            "id",
            "FleetDMTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_vuln_rels
    )

    # Assert FleetDMVulnerability nodes have Finding and Risk labels
    result = neo4j_session.run(
        """
        MATCH (n:FleetDMVulnerability:Finding:Risk)
        RETURN n.id AS id ORDER BY id
        """
    )
    vuln_ids = {record["id"] for record in result}
    assert vuln_ids == {"1-CVE-2024-1234", "2-CVE-2024-5678"}

    # Assert Vulnerability properties are correct
    nodes = check_nodes(
        neo4j_session,
        "FleetDMVulnerability",
        [
            "id",
            "details_link",
            "epss_probability",
            "resolved_in_version",
            "cve_published",
            "cve_description",
        ],
    )
    assert nodes == {
        (
            "1-CVE-2024-1234",
            "https://nvd.nist.gov/vuln/detail/CVE-2024-1234",
            0.5,
            "8.10.37",
            "2024-01-15T00:00:00Z",
            "Sample vulnerability in 1password",
        ),
        (
            "2-CVE-2024-5678",
            "https://nvd.nist.gov/vuln/detail/CVE-2024-5678",
            0.001,
            "124.0.6367.91",
            "2024-03-01T00:00:00Z",
            "Chromium heap overflow",
        ),
    }

    # Assert openssl version has 0 vulnerabilities_count
    openssl_result = neo4j_session.run(
        """
        MATCH (n:FleetDMSoftwareVersion {id: '3', name: 'openssl'})
        RETURN n.vulnerabilities_count AS count
        """
    )
    row = openssl_result.single()
    assert row is not None and row["count"] == 0


@patch.object(
    cartography.intel.fleetdm.versions,
    "get",
    return_value=tests.data.fleetdm.versions.MOCK_VERSIONS_RESPONSE,
)
def test_fleetdm_versions_cleanup(mock_api, neo4j_session):
    session = requests.Session()

    # Arrange - create tenant node first
    _create_tenant(neo4j_session)

    # Act - load with first update tag
    cartography.intel.fleetdm.versions.sync(
        neo4j_session,
        session,
        TEST_TENANT_ID,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert - 3 versions and 2 vulns loaded
    initial_versions = check_nodes(neo4j_session, "FleetDMSoftwareVersion", ["id"])
    assert initial_versions is not None and len(initial_versions) == 3
    initial_vulns = check_nodes(neo4j_session, "FleetDMVulnerability", ["id"])
    assert initial_vulns is not None and len(initial_vulns) == 2

    # Act - sync with newer tag, empty data
    NEW_UPDATE_TAG = 999999999
    with patch.object(
        cartography.intel.fleetdm.versions,
        "get",
        return_value=[],
    ):
        cartography.intel.fleetdm.versions.sync(
            neo4j_session,
            session,
            TEST_TENANT_ID,
            TEST_TENANT_ID,
            NEW_UPDATE_TAG,
            {"UPDATE_TAG": NEW_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
        )

    # Assert - stale versions and vulns cleaned up (0 remaining)
    remaining_versions = check_nodes(
        neo4j_session,
        "FleetDMSoftwareVersion",
        ["id"],
    )
    assert remaining_versions is None or len(remaining_versions) == 0
    remaining_vulns = check_nodes(
        neo4j_session,
        "FleetDMVulnerability",
        ["id"],
    )
    assert remaining_vulns is None or len(remaining_vulns) == 0
