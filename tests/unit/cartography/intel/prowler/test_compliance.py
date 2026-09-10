from typing import Any
from unittest.mock import MagicMock

import pytest

from cartography.intel.prowler import api
from cartography.intel.prowler import compliance

API_URL = "https://api.prowler.example"
PROVIDER_ID = "11111111-1111-4111-8111-111111111111"
OTHER_PROVIDER_ID = "22222222-2222-4222-8222-222222222222"


def _credential() -> api.ProwlerCredential:
    return api.ProwlerCredential(API_URL, api_key="test-key")


def _overview(**attributes: Any) -> dict[str, Any]:
    return {
        "type": "compliance-overviews",
        "attributes": {
            "id": "cis_2.0_aws",
            "framework": "CIS",
            "version": "2.0",
            "requirements_passed": 40,
            "requirements_failed": 5,
            "requirements_manual": 2,
            "total_requirements": 47,
            **attributes,
        },
    }


def _entry(
    provider_id: str = PROVIDER_ID,
    overview: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "provider_id": provider_id,
        "overview": _overview() if overview is None else overview,
    }


def _document(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"data": rows, "links": {"next": None}}


def test_transform_scopes_the_node_id_to_the_provider() -> None:
    # Arrange
    entries = [_entry()]

    # Act
    result = compliance.transform(entries)

    # Assert
    assert result[0]["id"] == f"{PROVIDER_ID}:cis_2.0_aws"
    assert result[0]["compliance_id"] == "cis_2.0_aws"


def test_transform_keeps_the_same_framework_distinct_per_provider() -> None:
    """Two providers assessed against one framework must not merge into one node."""
    # Arrange
    entries = [_entry(), _entry(provider_id=OTHER_PROVIDER_ID)]

    # Act
    result = compliance.transform(entries)

    # Assert
    assert [row["id"] for row in result] == [
        f"{PROVIDER_ID}:cis_2.0_aws",
        f"{OTHER_PROVIDER_ID}:cis_2.0_aws",
    ]
    assert len({row["id"] for row in result}) == 2


def test_transform_carries_the_provider_id_onto_the_row() -> None:
    # Arrange
    entries = [_entry()]

    # Act
    result = compliance.transform(entries)

    # Assert
    assert result[0]["provider_id"] == PROVIDER_ID


def test_transform_carries_the_framework_and_version() -> None:
    # Arrange
    entries = [_entry()]

    # Act
    result = compliance.transform(entries)

    # Assert
    assert result[0]["framework"] == "CIS"
    assert result[0]["version"] == "2.0"


def test_transform_carries_the_requirement_counts() -> None:
    # Arrange
    entries = [_entry()]

    # Act
    result = compliance.transform(entries)

    # Assert
    assert result[0]["requirements_passed"] == 40
    assert result[0]["requirements_failed"] == 5
    assert result[0]["requirements_manual"] == 2
    assert result[0]["total_requirements"] == 47


@pytest.mark.parametrize(  # type: ignore[misc]
    "field",
    [
        "requirements_passed",
        "requirements_failed",
        "requirements_manual",
        "total_requirements",
    ],
)
def test_transform_preserves_a_zero_count(field: str) -> None:
    """A zero is meaningful posture data and must not be flattened to None."""
    # Arrange
    entries = [_entry(overview=_overview(**{field: 0}))]

    # Act
    result = compliance.transform(entries)

    # Assert
    assert result[0][field] == 0
    assert result[0][field] is not None


@pytest.mark.parametrize("field", ["framework", "version"])  # type: ignore[misc]
def test_transform_absent_optional_string_becomes_none(field: str) -> None:
    # Arrange
    entries = [_entry(overview=_overview(**{field: None}))]

    # Act
    result = compliance.transform(entries)

    # Assert
    assert result[0][field] is None


@pytest.mark.parametrize("malformed_attributes", [None, [], "", 0, False])  # type: ignore[misc]
def test_transform_rejects_malformed_attributes(malformed_attributes: Any) -> None:
    # Arrange
    entries = [
        {
            "provider_id": PROVIDER_ID,
            "overview": {"attributes": malformed_attributes},
        },
    ]

    # Act and assert
    with pytest.raises(ValueError, match="attributes must be an object"):
        compliance.transform(entries)


def test_transform_rejects_an_overview_without_attributes() -> None:
    # Arrange
    entries = [{"provider_id": PROVIDER_ID, "overview": {"type": "x"}}]

    # Act and assert
    with pytest.raises(ValueError, match="attributes must be an object"):
        compliance.transform(entries)


@pytest.mark.parametrize("missing_id", [None, "", "   "])  # type: ignore[misc]
def test_transform_rejects_a_missing_compliance_id(missing_id: Any) -> None:
    # Arrange
    entries = [_entry(overview=_overview(id=missing_id))]

    # Act and assert
    with pytest.raises(ValueError, match="overview.id must be a nonempty string"):
        compliance.transform(entries)


def test_get_issues_one_request_per_provider(mocker) -> None:
    # Arrange
    sent: list[dict[str, Any]] = []

    def request(session, method, url, *, params=None, **kwargs) -> dict[str, Any]:
        sent.append(dict(params or {}))
        return _document([_overview()])

    mocker.patch.object(api, "_request_json", side_effect=request)

    # Act
    compliance.get(
        MagicMock(),
        API_URL,
        _credential(),
        [PROVIDER_ID, OTHER_PROVIDER_ID],
    )

    # Assert
    assert len(sent) == 2
    assert [params["filter[provider_id]"] for params in sent] == [
        PROVIDER_ID,
        OTHER_PROVIDER_ID,
    ]


def test_get_pairs_each_overview_with_its_provider(mocker) -> None:
    # Arrange
    def request(session, method, url, *, params=None, **kwargs) -> dict[str, Any]:
        provider_id = params["filter[provider_id]"]
        return _document([_overview(id=f"cis_2.0_{provider_id}")])

    mocker.patch.object(api, "_request_json", side_effect=request)

    # Act
    results = compliance.get(
        MagicMock(),
        API_URL,
        _credential(),
        [PROVIDER_ID, OTHER_PROVIDER_ID],
    )

    # Assert
    assert [entry["provider_id"] for entry in results] == [
        PROVIDER_ID,
        OTHER_PROVIDER_ID,
    ]
    assert [entry["overview"]["attributes"]["id"] for entry in results] == [
        f"cis_2.0_{PROVIDER_ID}",
        f"cis_2.0_{OTHER_PROVIDER_ID}",
    ]
