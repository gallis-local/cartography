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
