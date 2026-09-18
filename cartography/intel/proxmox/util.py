"""
Shared helpers for the Proxmox intel modules.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Proxmox answers with these when the API token lacks a required privilege.
_PERMISSION_STATUS_CODES = frozenset({401, 403})

# Proxmox answers with these when an optional feature (SDN, HA, replication, ...) is
# simply not present on the deployment, which is a normal thing to find.
_NOT_AVAILABLE_STATUS_CODES = frozenset({404, 501})


def _status_code(exception: Exception) -> int | None:
    """
    Best-effort extraction of an HTTP status code from a Proxmox API exception.

    ``proxmoxer.core.ResourceException`` carries ``status_code`` directly;
    ``requests`` exceptions carry it on the attached response.

    :param exception: Exception raised by a Proxmox API call
    :return: The HTTP status code, or None if it could not be determined
    """
    status = getattr(exception, "status_code", None)
    if isinstance(status, int):
        return status

    response = getattr(exception, "response", None)
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) else None


def is_permission_error(exception: Exception) -> bool:
    """
    Report whether a Proxmox API exception was an authorization refusal.

    Callers that fetch the same optional resource once per user or per guest use this
    to aggregate a single summary warning instead of emitting one per item.

    :param exception: Exception raised by a Proxmox API call
    :return: True if Proxmox refused the call for lack of privilege
    """
    return _status_code(exception) in _PERMISSION_STATUS_CODES


def log_optional_fetch_failure(
    exception: Exception,
    description: str,
    **context: Any,
) -> None:
    """
    Log a failed best-effort Proxmox fetch at a level that reflects its cause.

    These fetches all return an empty list on failure so one missing privilege or
    one absent feature does not abort the whole sync. The danger is that "the API
    refused us" and "there is genuinely nothing here" then look identical in the
    graph: both produce zero nodes. Logging a permission problem at WARNING keeps
    that distinction visible, because a silently incomplete graph is worse than a
    loud failure -- an operator who sees zero ``ProxmoxAPIToken`` nodes needs to
    know whether that means "no tokens exist" or "we were not allowed to look".

    :param exception: Exception raised by the Proxmox API call
    :param description: Human-readable description of what was being fetched
    :param context: Extra key/value pairs to include in the log message
    """
    suffix = "".join(f" ({k}={v})" for k, v in context.items())
    status = _status_code(exception)

    if status in _PERMISSION_STATUS_CODES:
        logger.warning(
            "Permission denied fetching %s%s: %s. The Proxmox sync token is missing a "
            "required privilege, so this data will be ABSENT from the graph rather "
            "than empty. Grant the privilege or scope the sync to avoid silently "
            "incomplete results.",
            description,
            suffix,
            exception,
        )
    elif status in _NOT_AVAILABLE_STATUS_CODES:
        logger.debug(
            "%s%s is not available on this Proxmox deployment: %s",
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
