import cartography.intel.fleetdm.labels as labels
import tests.data.fleetdm.labels as test_data


def test_transform_labels():
    result = labels.transform(test_data.MOCK_LABELS_RESPONSE["labels"])

    assert len(result) == 3
    ids = {label["id"] for label in result}
    assert ids == {"1", "2", "3"}
    names = {label["name"] for label in result}
    assert names == {"All Hosts", "macOS", "Ubuntu Linux"}


def test_transform_labels_empty():
    assert labels.transform([]) == []
