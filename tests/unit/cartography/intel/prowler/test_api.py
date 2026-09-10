from typing import Any
from unittest.mock import MagicMock

import pytest

import cartography.intel.prowler
from cartography.intel.prowler import api

API_URL = "https://api.prowler.example"


def _document(
    rows: list[dict[str, Any]],
    *,
    next_url: str | None = None,
) -> dict[str, Any]:
    return {"data": rows, "links": {"next": next_url, "prev": None}}


def _credential() -> api.ProwlerCredential:
    return api.ProwlerCredential(API_URL, api_key="test-key")


@pytest.mark.parametrize(
    ("api_url", "api_key", "email", "password"),
    [
        (None, "test-key", None, None),
        (API_URL, None, None, None),
        (API_URL, None, "user@example.com", None),
        (API_URL, None, None, "test-password"),
    ],
)  # type: ignore[misc]
def test_start_prowler_ingestion_skips_incomplete_config(
    mocker,
    api_url: str | None,
    api_key: str | None,
    email: str | None,
    password: str | None,
) -> None:
    # Arrange
    config = MagicMock(
        prowler_api_url=api_url,
        prowler_api_key=api_key,
        prowler_email=email,
        prowler_password=password,
    )
    create_session = mocker.patch.object(api, "create_session")

    # Act
    cartography.intel.prowler.start_prowler_ingestion(MagicMock(), config)

    # Assert
    create_session.assert_not_called()


def test_start_prowler_ingestion_skips_invalid_api_url(mocker) -> None:
    # Arrange
    config = MagicMock(
        prowler_api_url="not-an-api-origin",
        prowler_api_key="test-key",
        prowler_email=None,
        prowler_password=None,
    )
    create_session = mocker.patch.object(api, "create_session")

    # Act
    cartography.intel.prowler.start_prowler_ingestion(MagicMock(), config)

    # Assert
    create_session.assert_not_called()


@pytest.mark.parametrize(
    "api_url",
    [
        "http://prowler.example.com",
        "https://api.prowler.example/api/v1",
        "https://user:pass@api.prowler.example",
        "ftp://api.prowler.example",
        "api.prowler.example",
    ],
)  # type: ignore[misc]
def test_normalize_api_url_rejects_unusable_origins(api_url: str) -> None:
    with pytest.raises(ValueError):
        api.normalize_api_url(api_url)


@pytest.mark.parametrize(
    ("api_url", "expected"),
    [
        ("https://api.prowler.com", "https://api.prowler.com"),
        ("  https://api.prowler.com/  ", "https://api.prowler.com"),
        ("http://localhost:8080", "http://localhost:8080"),
        ("http://127.0.0.1:8080", "http://127.0.0.1:8080"),
    ],
)  # type: ignore[misc]
def test_normalize_api_url_accepts_supported_origins(
    api_url: str,
    expected: str,
) -> None:
    assert api.normalize_api_url(api_url) == expected


def test_auth_header_uses_the_api_key_keyword() -> None:
    # The API documents `Api-Key <key>` for keys and `Bearer <token>` for JWTs.
    assert _credential().auth_header() == "Api-Key test-key"
    jwt = api.ProwlerCredential(API_URL, access_token="test-token")
    assert jwt.auth_header() == "Bearer test-token"


def test_iter_resources_follows_the_next_link(mocker) -> None:
    # Arrange
    page_two = f"{API_URL}/api/v1/providers?page%5Bnumber%5D=2"
    documents = [
        _document([{"id": "1"}], next_url=page_two),
        _document([{"id": "2"}]),
    ]
    mocker.patch.object(api, "_request_json", side_effect=documents)

    # Act
    rows = list(
        api.iter_resources(
            MagicMock(),
            API_URL,
            _credential(),
            api.PROVIDERS_PATH,
            result_name="providers",
        ),
    )

    # Assert
    assert [row["id"] for row in rows] == ["1", "2"]


def test_iter_pages_rejects_a_repeated_page(mocker) -> None:
    # Arrange: a next link that points back at the page we just read.
    first = f"{API_URL}{api.PROVIDERS_PATH}"
    mocker.patch.object(
        api,
        "_request_json",
        side_effect=[_document([{"id": "1"}], next_url=first)],
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="repeated a page"):
        list(
            api.iter_resources(
                MagicMock(),
                API_URL,
                _credential(),
                api.PROVIDERS_PATH,
                result_name="providers",
            ),
        )


def test_iter_pages_retries_without_page_size_when_rejected(mocker) -> None:
    """`page[size]` is undocumented on the /latest endpoints.

    A 400 naming it must be treated as "this endpoint does not take it" rather
    than failing the sync.
    """
    # Arrange
    sent: list[dict[str, Any]] = []

    def request(session, method, url, *, params=None, **kwargs):
        sent.append(dict(params or {}))
        if params and "page[size]" in params:
            raise RuntimeError(
                "Prowler GET /api/v1/findings/latest failed with HTTP 400: "
                "invalid query parameter: page[size]",
            )
        return _document([{"id": "1"}])

    mocker.patch.object(api, "_request_json", side_effect=request)

    # Act
    rows = list(
        api.iter_resources(
            MagicMock(),
            API_URL,
            _credential(),
            api.FINDINGS_PATH,
            params={"include": "resources"},
            result_name="findings",
        ),
    )

    # Assert
    assert [row["id"] for row in rows] == ["1"]
    assert sent == [
        {"include": "resources", "page[size]": api.PAGE_SIZE},
        {"include": "resources"},
    ]


def test_iter_pages_does_not_mask_other_bad_requests(mocker) -> None:
    # Arrange
    mocker.patch.object(
        api,
        "_request_json",
        side_effect=RuntimeError(
            "Prowler GET /api/v1/findings/latest failed with HTTP 400"
        ),
    )

    # Act and assert: a 400 that does not name a page parameter is a real error.
    with pytest.raises(RuntimeError, match="HTTP 400"):
        list(
            api.iter_resources(
                MagicMock(),
                API_URL,
                _credential(),
                api.FINDINGS_PATH,
                result_name="findings",
            ),
        )


def test_page_rows_accepts_a_single_object() -> None:
    """The published schema types the /latest collections as a single object.

    drf-spectacular mis-introspects their `detail=False` action, so accept both
    shapes rather than betting on which one the deployment returns.
    """
    row = {"id": "1", "type": "findings"}
    assert api.page_rows({"data": row}, "findings") == [row]
    assert api.page_rows({"data": [row]}, "findings") == [row]


def test_page_rows_rejects_a_malformed_payload() -> None:
    with pytest.raises(ValueError):
        api.page_rows({"data": "not-a-list"}, "findings")
    with pytest.raises(ValueError):
        api.page_rows({"data": ["not-an-object"]}, "findings")


def test_refresh_replaces_both_tokens(mocker) -> None:
    """Prowler rotates refresh tokens and blacklists the previous one."""
    # Arrange
    credential = api.ProwlerCredential(
        API_URL,
        access_token="old-access",
        refresh_token="old-refresh",
    )
    mocker.patch.object(
        api,
        "_request_json",
        return_value={
            "data": {
                "type": "tokens-refresh",
                "attributes": {"access": "new-access", "refresh": "new-refresh"},
            },
        },
    )
    session = MagicMock()
    session.headers = {}

    # Act
    credential.refresh(session)

    # Assert
    assert credential.auth_header() == "Bearer new-access"
    assert session.headers["Authorization"] == "Bearer new-access"
    # A second refresh must present the rotated token, not the blacklisted one.
    assert credential._refresh_token == "new-refresh"


def test_api_key_credential_is_not_refreshable() -> None:
    assert _credential().refreshable is False
    assert (
        api.ProwlerCredential(
            API_URL,
            access_token="a",
            refresh_token="r",
        ).refreshable
        is True
    )
