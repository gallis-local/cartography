import cartography.intel.fleetdm.users as users
import tests.data.fleetdm.users as test_data


def test_transform_users():
    result = users.transform(test_data.MOCK_USERS_RESPONSE["users"])

    assert len(result) == 2
    admin = next(u for u in result if u["id"] == "1")
    assert admin["email"] == "admin@example.com"
    assert admin["global_role"] == "admin"
    assert admin["mfa_enabled"] is True


def test_transform_users_empty():
    assert users.transform([]) == []
