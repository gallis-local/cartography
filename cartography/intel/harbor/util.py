import logging
from typing import Any
from urllib.parse import quote
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v2.0"
PAGE_SIZE = 100
# Harbor's maximum page_size is 100; requests below it still return every row.
_RETRY_STATUS_CODES = (408, 429, *range(500, 600))
_RETRY_TOTAL = 4
_RETRY_BACKOFF_FACTOR = 1
_RETRY_BACKOFF_MAX = 16
_TIMEOUT = (60, 60)

VULNERABILITY_REPORT_MIME_PREFIX = "application/vnd.security.vulnerability.report"


def normalize_base_url(url: str) -> tuple[str, str]:
    """
    Validate the configured Harbor URL.

    :return: The base URL without a trailing slash, and the instance id (the
        lowercased host[:port]), which is also the registry host that images are
        pulled from.
    """
    parsed = urlsplit(url.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(
            "Harbor URL must be an https URL such as https://harbor.example.com."
        )
    if parsed.query or parsed.fragment or parsed.path.strip("/"):
        raise ValueError("Harbor URL must not include a path, query, or fragment.")
    instance_id = parsed.netloc.lower()
    return f"https://{instance_id}", instance_id


def create_session(username: str, password: str, verify_ssl: bool) -> requests.Session:
    """Build a read-only session with bounded retries and basic auth."""
    session = requests.Session()
    session.auth = (username, password)
    session.verify = verify_ssl
    session.headers.update({"Accept": "application/json"})
    retry_policy = Retry(
        total=_RETRY_TOTAL,
        connect=_RETRY_TOTAL,
        read=_RETRY_TOTAL,
        status=_RETRY_TOTAL,
        other=0,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=_RETRY_STATUS_CODES,
        backoff_factor=_RETRY_BACKOFF_FACTOR,
        backoff_max=_RETRY_BACKOFF_MAX,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session


def encode_repository_name(repository_name: str) -> str:
    """
    Encode a repository name for a Harbor URL path segment.

    Harbor repository names can contain slashes (`team/app`), and the API wants
    each slash double-encoded (`team%252Fapp`).
    """
    return quote(quote(repository_name, safe=""), safe="")


def get_json(
    session: requests.Session,
    base_url: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> Any:
    # Harbor never redirects API calls; refusing redirects keeps the credential
    # from being replayed to another host.
    response = session.get(
        f"{base_url}{API_PREFIX}{path}",
        params=params,
        timeout=_TIMEOUT,
        allow_redirects=False,
    )
    response.raise_for_status()
    return response.json()


def get_paginated(
    session: requests.Session,
    base_url: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fetch a complete page/page_size collection before loading or cleanup."""
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = get_json(
            session,
            base_url,
            path,
            {**(params or {}), "page": page, "page_size": PAGE_SIZE},
        )
        results.extend(batch)
        if len(batch) < PAGE_SIZE:
            return results
        page += 1


def pick_report(payload: dict[str, Any], mime_prefix: str) -> dict[str, Any] | None:
    """
    Harbor keys scan reports by MIME type, with a version suffix that differs between
    scanners and Harbor releases. Return the first report whose key starts with
    `mime_prefix`.
    """
    for mime_type, report in payload.items():
        if mime_type.startswith(mime_prefix) and isinstance(report, dict):
            return report
    return None
