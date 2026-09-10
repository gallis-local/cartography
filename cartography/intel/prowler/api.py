import logging
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cartography.intel.prowler.response import require_list
from cartography.intel.prowler.response import require_nonempty_string
from cartography.intel.prowler.response import require_object

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 120
REQUEST_TIMEOUT = (CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS)

JSON_API_CONTENT_TYPE = "application/vnd.api+json"
API_ROOT = "/api/v1"
TOKENS_PATH = f"{API_ROOT}/tokens"
TOKENS_REFRESH_PATH = f"{API_ROOT}/tokens/refresh"
TENANTS_PATH = f"{API_ROOT}/tenants"
PROVIDERS_PATH = f"{API_ROOT}/providers"
SCANS_PATH = f"{API_ROOT}/scans"
# The `/latest` variants report the current state of the most recent scan per
# provider. Unlike `/findings` and `/resources` they take no mandatory date
# filter and are not subject to the API's maximum date-range window.
FINDINGS_PATH = f"{API_ROOT}/findings/latest"
RESOURCES_PATH = f"{API_ROOT}/resources/latest"

# The API silently clamps page[size] to 100.
PAGE_SIZE = 100
MAX_PAGES = 10_000
_PROGRESS_PAGE_INTERVAL = 10
_RETRY_STATUS_CODES = (408, 429, 502, 503, 504)


def normalize_api_url(api_url: str) -> str:
    """Validate and normalize the origin of a Prowler API deployment."""
    parsed = urlparse(api_url.strip())
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        raise ValueError("Prowler API URL must be an absolute HTTP(S) origin")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Prowler API URL must not contain user information")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Prowler API URL contains an invalid port") from exc
    if parsed.path.rstrip("/") or parsed.params or parsed.query or parsed.fragment:
        raise ValueError(
            "Prowler API URL must be an origin without /api, a route, query, or fragment",
        )
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1"):
        # Self-hosted Prowler is commonly reached over plaintext on loopback, but
        # sending a bearer credential over plaintext to a remote host is not safe.
        raise ValueError(
            "Prowler API URL must use https except when pointing at localhost",
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def create_session() -> requests.Session:
    """Create a Prowler API session with bounded retries for read-only requests."""
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        other=0,
        allowed_methods=frozenset({"GET", "POST"}),
        status_forcelist=_RETRY_STATUS_CODES,
        backoff_factor=0.25,
        backoff_max=16,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(
        {
            "Accept": JSON_API_CONTENT_TYPE,
            "Content-Type": JSON_API_CONTENT_TYPE,
            "User-Agent": "cartography-prowler",
        },
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _describe_errors(payload: Any) -> str | None:
    """Summarize a JSON:API error document for logging."""
    if not isinstance(payload, dict):
        return None
    errors = payload.get("errors")
    if not isinstance(errors, list):
        return None
    details = [
        error["detail"]
        for error in errors
        if isinstance(error, dict) and isinstance(error.get("detail"), str)
    ]
    return "; ".join(details) or None


def _request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    redact_path: str | None = None,
) -> dict[str, Any]:
    """Issue one Prowler API request and return its JSON:API document.

    `redact_path` names the request in error messages for calls whose URL or body
    carries a credential, so nothing sensitive reaches the logs.
    """
    label = redact_path if redact_path is not None else f"{method} {urlparse(url).path}"
    try:
        response = session.request(
            method,
            url,
            params=params,
            json=json_body,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Prowler {label} request failed") from exc

    if response.status_code >= 400:
        try:
            detail = _describe_errors(response.json())
        except ValueError:
            detail = None
        message = f"Prowler {label} failed with HTTP {response.status_code}"
        if detail:
            message = f"{message}: {detail}"
        raise RuntimeError(message)

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Prowler {label} returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Prowler {label} returned a non-object response")
    return payload


def _token_attributes(payload: dict[str, Any], label: str) -> tuple[str, str]:
    """Return the access and refresh tokens in a Prowler token document."""
    data = require_object(payload.get("data"), f"Prowler {label} data")
    attributes = require_object(data.get("attributes"), f"Prowler {label} attributes")
    access = require_nonempty_string(
        attributes.get("access"), f"Prowler {label} access"
    )
    refresh = require_nonempty_string(
        attributes.get("refresh"),
        f"Prowler {label} refresh",
    )
    return access, refresh


class ProwlerCredential:
    """Holds the Authorization header for a Prowler API session.

    An API key is a long-lived static credential. A JWT access token expires after
    about 30 minutes, so `refresh()` exchanges the refresh token for a new pair
    mid-sync. Prowler rotates refresh tokens and blacklists the previous one, so
    the newly issued refresh token replaces the stored one on every exchange.
    """

    def __init__(
        self,
        api_url: str,
        *,
        api_key: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        if api_key is None and access_token is None:
            raise ValueError(
                "Prowler credential requires an API key or an access token"
            )
        self._api_url = api_url
        self._api_key = api_key
        self._access_token = access_token
        self._refresh_token = refresh_token

    @property
    def refreshable(self) -> bool:
        return self._api_key is None and self._refresh_token is not None

    def auth_header(self) -> str:
        if self._api_key is not None:
            return f"Api-Key {self._api_key}"
        return f"Bearer {self._access_token}"

    def apply(self, session: requests.Session) -> None:
        session.headers["Authorization"] = self.auth_header()

    def refresh(self, session: requests.Session) -> None:
        """Exchange the refresh token for a new access and refresh token pair."""
        if self._refresh_token is None:
            raise RuntimeError("Prowler credential cannot be refreshed")
        payload = _request_json(
            session,
            "POST",
            f"{self._api_url}{TOKENS_REFRESH_PATH}",
            json_body={
                "data": {
                    "type": "tokens-refresh",
                    "attributes": {"refresh": self._refresh_token},
                },
            },
            redact_path="POST /api/v1/tokens/refresh",
        )
        self._access_token, self._refresh_token = _token_attributes(
            payload,
            "token refresh",
        )
        self.apply(session)


def authenticate_with_password(
    session: requests.Session,
    api_url: str,
    email: str,
    password: str,
    tenant_id: str | None = None,
) -> ProwlerCredential:
    """Exchange a Prowler email and password for a JWT credential."""
    attributes: dict[str, Any] = {"email": email, "password": password}
    if tenant_id:
        attributes["tenant_id"] = tenant_id
    payload = _request_json(
        session,
        "POST",
        f"{api_url}{TOKENS_PATH}",
        json_body={"data": {"type": "tokens", "attributes": attributes}},
        redact_path="POST /api/v1/tokens",
    )
    access, refresh = _token_attributes(payload, "token")
    credential = ProwlerCredential(
        api_url,
        access_token=access,
        refresh_token=refresh,
    )
    credential.apply(session)
    return credential


def get_tenants(
    session: requests.Session,
    api_url: str,
    credential: ProwlerCredential,
) -> list[dict[str, Any]]:
    """Return the tenants the credential can see."""
    return list(
        iter_resources(
            session, api_url, credential, TENANTS_PATH, result_name="tenants"
        )
    )


def _request_document(
    session: requests.Session,
    url: str,
    credential: ProwlerCredential,
    *,
    params: dict[str, Any] | None,
    result_name: str,
) -> dict[str, Any]:
    """Fetch one JSON:API document, refreshing an expired JWT once and retrying."""
    try:
        return _request_json(session, "GET", url, params=params)
    except RuntimeError as exc:
        if "HTTP 401" not in str(exc) or not credential.refreshable:
            raise
        logger.debug(
            "Prowler access token expired while fetching %s, refreshing.",
            result_name,
        )
        credential.refresh(session)
        return _request_json(session, "GET", url, params=params)


def _is_page_param_error(exc: Exception) -> bool:
    """Whether a 400 looks like the API rejecting our page[size] parameter."""
    message = str(exc)
    return "HTTP 400" in message and "page" in message.lower()


def page_rows(document: dict[str, Any], result_name: str) -> list[dict[str, Any]]:
    """Return a document's primary resource objects as a list.

    The published OpenAPI schema types the `/latest` collections as returning a
    single object rather than an array, because drf-spectacular mis-introspects
    their `detail=False` action. They return an array in practice, so accept
    either shape rather than betting on which one is right.
    """
    data = document.get("data")
    if isinstance(data, dict):
        return [data]
    rows = require_list(data, f"Prowler {result_name} data")
    return [require_object(row, f"Prowler {result_name} item") for row in rows]


def iter_pages(
    session: requests.Session,
    api_url: str,
    credential: ProwlerCredential,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    result_name: str,
    max_pages: int = MAX_PAGES,
) -> Iterator[dict[str, Any]]:
    """Yield each JSON:API document of a paginated Prowler collection.

    Pagination follows `links.next`, which the API returns as an absolute URL and
    sets to null on the final page. Yielding whole documents rather than rows lets
    callers read the sideloaded `included` array alongside `data`.

    `page[size]` is documented on the plain collections but not on the `/latest`
    ones, so a rejection of it is treated as "this endpoint does not take it":
    the request is retried without it and the smaller default page size is used
    from then on. Following `links.next` means paging still works either way, and
    an endpoint that does not paginate at all simply yields one document.
    """
    if max_pages < 1:
        raise ValueError("Prowler max_pages must be greater than zero")

    query: dict[str, Any] | None = {**(params or {}), "page[size]": PAGE_SIZE}
    url = f"{api_url}{path}"
    page_count = 0
    seen_urls: set[str] = set()

    while True:
        if page_count >= max_pages:
            raise RuntimeError(
                f"Prowler {result_name} pagination exceeded {max_pages} pages",
            )
        if url in seen_urls:
            raise RuntimeError(f"Prowler {result_name} pagination repeated a page")
        seen_urls.add(url)

        try:
            document = _request_document(
                session,
                url,
                credential,
                params=query,
                result_name=result_name,
            )
        except RuntimeError as exc:
            if query is None or "page[size]" not in query:
                raise
            if not _is_page_param_error(exc):
                raise
            logger.debug(
                "Prowler %s rejected page[size], retrying without it.",
                result_name,
            )
            query = {key: value for key, value in query.items() if key != "page[size]"}
            document = _request_document(
                session,
                url,
                credential,
                params=query,
                result_name=result_name,
            )
        page_rows(document, result_name)
        page_count += 1
        yield document

        if page_count % _PROGRESS_PAGE_INTERVAL == 0:
            logger.debug(
                "Fetched %d pages of Prowler %s.",
                page_count,
                result_name,
            )

        links = document.get("links")
        next_url = links.get("next") if isinstance(links, dict) else None
        if next_url is None:
            return
        if not isinstance(next_url, str) or not next_url.strip():
            raise RuntimeError(f"Prowler {result_name} returned a malformed next link")
        url = next_url
        # `links.next` already carries the full query string.
        query = None


def iter_resources(
    session: requests.Session,
    api_url: str,
    credential: ProwlerCredential,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    result_name: str,
) -> Iterator[dict[str, Any]]:
    """Yield each primary resource object of a paginated Prowler collection."""
    for document in iter_pages(
        session,
        api_url,
        credential,
        path,
        params=params,
        result_name=result_name,
    ):
        yield from page_rows(document, result_name)
