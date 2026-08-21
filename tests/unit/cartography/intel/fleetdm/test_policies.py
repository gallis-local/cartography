import cartography.intel.fleetdm.policies as policies
import tests.data.fleetdm.policies as test_data


def test_transform_policies():
    result = policies.transform(test_data.MOCK_POLICIES_RESPONSE["policies"])

    assert len(result) == 2
    policy_1 = next(p for p in result if p["id"] == "1")
    assert policy_1["name"] == "Gatekeeper enabled"
    assert policy_1["author_id"] == "1"
    assert policy_1["team_id"] is None


def test_transform_policies_missing_optional_ids():
    raw = [
        {
            "id": 42,
            "name": "no-author-policy",
            "author_id": None,
            "team_id": None,
        }
    ]
    result = policies.transform(raw)

    assert len(result) == 1
    assert result[0]["author_id"] is None
    assert result[0]["team_id"] is None


def test_transform_policies_empty():
    assert policies.transform([]) == []
