import logging
from typing import Any
from typing import Generator

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)

# Fleet answers with these when the endpoint exists but the current license tier or
# the token's role does not allow the call. 402 is Fleet's "requires Fleet Premium".
_LICENSE_STATUS_CODES = frozenset({402, 403})

# Fleet answers with these when the feature is simply not present on the deployment.
_NOT_AVAILABLE_STATUS_CODES = frozenset({404, 501})


def _status_code(exception: Exception) -> int | None:
    """
    Best-effort extraction of an HTTP status code from a Fleet API exception.

    :param exception: Exception raised by a Fleet API call
    :return: The HTTP status code, or None if it could not be determined
    """
    response = getattr(exception, "response", None)
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) else None


def is_license_error(exception: Exception) -> bool:
    """
    Report whether Fleet refused a call because of license tier or role.

    Callers that fetch the same optional resource once per host or per policy use this
    to aggregate a single summary warning instead of emitting one line per item.

    :param exception: Exception raised by a Fleet API call
    :return: True if Fleet refused the call for license or permission reasons
    """
    return _status_code(exception) in _LICENSE_STATUS_CODES


def log_optional_fetch_failure(
    exception: Exception,
    description: str,
    **context: Any,
) -> None:
    """
    Log a failed best-effort Fleet fetch at a level that reflects its cause.

    These fetches fall back to an empty list so that one license-gated or absent
    endpoint does not abort the whole sync. The danger is that "Fleet refused us" and
    "there is genuinely nothing here" then look identical in the graph: both produce
    zero nodes. Logging a refusal at WARNING keeps that distinction visible, because
    an operator who sees zero ``FleetDMFleet`` nodes needs to know whether that means
    "no fleets exist" or "we were not allowed to look".

    :param exception: Exception raised by the Fleet API call
    :param description: Human-readable description of what was being fetched
    :param context: Extra key/value pairs to include in the log message
    """
    suffix = "".join(f" ({k}={v})" for k, v in context.items())
    status = _status_code(exception)

    if status in _LICENSE_STATUS_CODES:
        logger.warning(
            "Fleet refused the request for %s%s with HTTP %s: %s. This endpoint "
            "requires Fleet Premium or a more privileged API token, so this data "
            "will be ABSENT from the graph rather than empty.",
            description,
            suffix,
            status,
            exception,
        )
    elif status in _NOT_AVAILABLE_STATUS_CODES:
        logger.debug(
            "%s%s is not available on this Fleet deployment: %s",
            description,
            suffix,
            exception,
        )
    else:
        logger.warning(
            "Could not fetch %s%s: %s",
            description,
            suffix,
            exception,
        )


def paginated_get(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    page_size: int = 100,
) -> Generator[dict[str, Any], None, None]:
    """Helper to get paginated data from the FleetDM REST API.

    FleetDM uses page/per_page pagination. Some endpoints return a top-level
    array, others return a dict with a resource key and optional 'meta' object
    with 'has_next_results'.

    Auth headers, retry logic, and timeout should be configured on the session.
    """
    base_params: dict[str, Any] = dict(params or {})
    page = 0

    while True:
        request_params = {
            **base_params,
            "page": page,
            "per_page": page_size,
        }
        response = api_session.get(url, params=request_params, timeout=_TIMEOUT)
        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, list):
            page_len = len(payload)
            logger.debug(
                "paginated_get %s page=%d got %d items",
                url,
                page,
                page_len,
            )
            yield from payload
            if page_len < page_size:
                break
        else:
            # Try to find the resource list in the top-level keys.
            # Common patterns: {"hosts": [...]}, {"users": [...]}, etc.
            resource_list: list[dict[str, Any]] | None = None
            resource_key = _find_resource_key(payload)
            if resource_key:
                resource_list = payload[resource_key]

            if resource_list is None:
                logger.debug(
                    "paginated_get %s page=%d no resource list found, stopping",
                    url,
                    page,
                )
                break

            page_len = len(resource_list)
            logger.debug(
                "paginated_get %s page=%d got %d items",
                url,
                page,
                page_len,
            )
            yield from resource_list

            # Check meta.has_next_results if present
            meta = payload.get("meta", {})
            if meta.get("has_next_results") is False:
                break
            if page_len < page_size:
                break

        page += 1


def _find_resource_key(payload: dict[str, Any]) -> str | None:
    """Identify the key containing the resource list in a FleetDM API response.

    FleetDM endpoints return JSON with the resource key matching the endpoint,
    e.g. 'hosts', 'users', 'labels', 'policies', 'software_titles', 'fleets',
    'certificates', 'activities'.
    """
    known_keys = [
        "hosts",
        "users",
        "labels",
        "policies",
        "software_titles",
        "fleets",
        "certificates",
        "activities",
        "software",
        "software_versions",
        "teams",
    ]
    for key in known_keys:
        value = payload.get(key)
        if isinstance(value, list):
            return key
    return None
