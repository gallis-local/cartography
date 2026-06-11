import logging
from typing import Any
from typing import Generator

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)


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
