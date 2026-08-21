import cartography.intel.fleetdm.fleets as fleets
import tests.data.fleetdm.fleets as test_data


def test_transform_fleets():
    result = fleets.transform(test_data.MOCK_FLEETS_RESPONSE["fleets"])

    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[0]["name"] == "Production"
    assert result[1]["id"] == "2"
    assert result[1]["name"] == "Development"

    # ids must be stringified for consistent identity keys
    assert all(isinstance(fleet["id"], str) for fleet in result)


def test_transform_fleets_empty():
    assert fleets.transform([]) == []
