import re
from datetime import datetime
from typing import Any

from dateutil.parser import isoparse

_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


def require_object(value: Any, field: str) -> dict[str, Any]:
    """Return a required JSON object or reject the malformed field."""
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    """Return a required JSON array or reject the malformed field."""
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def require_nonempty_string(value: Any, field: str) -> str:
    """Return a normalized required string or reject the malformed field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value.strip()


def optional_nonempty_string(value: Any, field: str) -> str | None:
    """Normalize an optional string while rejecting malformed present values."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    normalized = value.strip()
    return normalized or None


def optional_string(value: Any, field: str) -> str | None:
    """Return an optional string or reject a malformed present value."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def optional_bool(value: Any, field: str) -> bool | None:
    """Return an optional boolean or reject a malformed present value."""
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def optional_number(value: Any, field: str) -> int | float | None:
    """Return an optional number or reject a malformed present value."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    return value


def optional_string_list(value: Any, field: str) -> list[str] | None:
    """Return the distinct nonempty strings in an optional array field."""
    if value is None:
        return None
    items = require_list(value, field)
    normalized: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise ValueError(f"{field} must contain only strings")
        candidate = item.strip()
        if candidate and candidate not in normalized:
            normalized.append(candidate)
    return normalized or None


def parse_datetime(value: Any, field: str) -> datetime | None:
    """Parse an optional Prowler RFC 3339 timestamp into a Neo4j-safe datetime."""
    if value is None:
        return None
    normalized = require_nonempty_string(value, field)
    try:
        timestamp = isoparse(normalized)
    except ValueError as exc:
        raise ValueError(f"{field} must be an RFC 3339 timestamp") from exc
    if timestamp.tzinfo is None:
        raise ValueError(f"{field} must include a UTC offset")
    return timestamp


def canonical_cve_ids(*values: Any) -> list[str]:
    """Return the distinct canonical CVE identifiers found in Prowler fields."""
    candidates: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            candidates.append(value)
            continue
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            candidates.extend(value)
            continue
        raise ValueError("Prowler CVE fields must contain strings")

    return sorted(
        {
            candidate.strip().upper()
            for candidate in candidates
            if _CVE_RE.fullmatch(candidate.strip())
        },
    )
