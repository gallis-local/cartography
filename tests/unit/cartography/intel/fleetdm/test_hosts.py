import cartography.intel.fleetdm.hosts as hosts
import tests.data.fleetdm.hosts as test_data


def test_transform_hosts():
    result = hosts.transform(test_data.MOCK_HOSTS_RESPONSE)

    assert len(result) == 2
    host_1 = next(h for h in result if h["id"] == "1")
    assert host_1["hostname"] == "dev-macbook-pro.local"
    assert host_1["fleet_id"] is None
    assert host_1["failing_policies_count"] == 2
    assert host_1["critical_vulnerabilities_count"] == 0

    host_2 = next(h for h in result if h["id"] == "2")
    assert host_2["fleet_id"] == "1"


def test_transform_hosts_missing_issues():
    raw = [
        {
            "id": 5,
            "hostname": "no-issues-host",
        }
    ]
    result = hosts.transform(raw)

    assert len(result) == 1
    assert result[0]["failing_policies_count"] is None
    assert result[0]["critical_vulnerabilities_count"] is None


def test_transform_hosts_empty():
    assert hosts.transform([]) == []
