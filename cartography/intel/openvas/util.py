"""
Shared helpers for the OpenVAS intel module.
"""

import logging
from typing import Any
from typing import Optional

logger = logging.getLogger(__name__)

# gvmd answers with these GMP status codes when the authenticated user lacks the
# permission to run a command or to see the resources it would return.
_PERMISSION_STATUS_CODES = frozenset({401, 403})

# gvmd answers with this when the command itself is unknown to the running gvmd
# version, which is a normal thing to find on an older GVM release.
_NOT_AVAILABLE_STATUS_CODES = frozenset({404})


def _status_code(exception: Exception) -> int | None:
    """
    Best-effort extraction of the GMP status code from a python-gvm exception.

    ``GvmResponseError``/``GvmServerError`` carry ``status`` as the raw string
    gvmd put in the response envelope (e.g. ``"403"``), not as an int.

    :param exception: Exception raised by a GMP call
    :return: The GMP status code, or None if it could not be determined
    """
    status = getattr(exception, "status", None)
    if isinstance(status, int):
        return status
    try:
        return int(str(status))
    except ValueError:
        return None


def is_permission_error(exception: Exception) -> bool:
    """
    Report whether a GMP exception was an authorization refusal.

    Callers that fetch the same optional resource once per item (per task, per
    report, ...) use this to aggregate a single summary warning instead of
    emitting one per item.

    :param exception: Exception raised by a GMP call
    :return: True if gvmd refused the call for lack of permission
    """
    return _status_code(exception) in _PERMISSION_STATUS_CODES


def log_optional_fetch_failure(
    exception: Exception,
    description: str,
    **context: Any,
) -> None:
    """
    Log a failed best-effort GMP fetch at a level that reflects its cause.

    These fetches return an empty list on failure so that one missing GVM
    permission does not abort the whole sync. The danger is that "gvmd refused
    us" and "there is genuinely nothing here" then look identical in the graph:
    both produce zero nodes. Logging a permission problem at WARNING keeps that
    distinction visible, because a silently incomplete vulnerability graph is
    worse than a loud failure -- an operator who sees zero ``OpenVASResult``
    nodes needs to know whether that means "no findings" or "we were not
    allowed to look".

    :param exception: Exception raised by the GMP call
    :param description: Human-readable description of what was being fetched
    :param context: Extra key/value pairs to include in the log message
    """
    suffix = "".join(f" ({k}={v})" for k, v in context.items())
    status = _status_code(exception)

    if status in _PERMISSION_STATUS_CODES:
        logger.warning(
            "Permission denied fetching %s%s: %s. The GVM sync user is missing a "
            "required permission, so this data will be ABSENT from the graph "
            "rather than empty. Grant the permission to avoid silently "
            "incomplete results.",
            description,
            suffix,
            exception,
        )
    elif status in _NOT_AVAILABLE_STATUS_CODES:
        logger.debug(
            "%s%s is not available on this GVM deployment: %s",
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


def float_or_none(value: Optional[str]) -> Optional[float]:
    """
    Coerce a GVM numeric string to a float, or None when absent or unparseable.

    Scores must be one type graph-wide: a CVSS score stored as the string "7.5"
    compares lexically in Cypher, so `WHERE n.severity > 7` silently matches
    "0.9" and misses "10.0".

    :param value: Raw element text, or None
    :return: The value as a float, or None
    """
    if value is None or not value.strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


def int_or_none(value: Optional[str]) -> Optional[int]:
    """
    Coerce a GVM integer string to an int, or None when absent or unparseable.

    :param value: Raw element text, or None
    :return: The value as an int, or None
    """
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError:
        return None


def bool_or_none(value: Optional[str]) -> Optional[bool]:
    """
    Coerce a GVM "0"/"1" flag to a bool, or None when the element is absent.

    GVM emits these flags as text. Left as strings they cannot be used in a
    Cypher predicate directly -- Neo4j needs a boolean there -- so every caller
    had to know to compare against the literal "1".

    :param value: Raw element text, or None
    :return: The flag as a bool, or None
    """
    if value is None or not value.strip():
        return None
    return value.strip() not in ("0", "false")
