import cartography.intel.fleetdm.software as software
import tests.data.fleetdm.software as test_data


def test_transform_software():
    result = software.transform(
        test_data.MOCK_SOFTWARE_RESPONSE["software_titles"],
    )

    assert len(result) == 2
    ids = {title["id"] for title in result}
    assert ids == {"100", "101"}
    slack = next(t for t in result if t["id"] == "100")
    assert slack["name"] == "Slack"
    assert slack["source"] == "apps"


def test_transform_software_empty():
    assert software.transform([]) == []


def test_transform_software_collects_version_ids():
    result = software.transform(
        test_data.MOCK_SOFTWARE_RESPONSE["software_titles"],
    )

    slack = next(t for t in result if t["id"] == "100")
    assert slack["software_version_ids"] == ["1001"]
    glibc = next(t for t in result if t["id"] == "101")
    assert glibc["software_version_ids"] == ["1002", "1003"]


def test_transform_software_without_versions():
    result = software.transform([{"id": 1, "name": "no-versions"}])

    assert result[0]["software_version_ids"] == []
