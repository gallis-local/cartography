from typing import Any

from cartography.intel.prowler.response import require_list
from cartography.intel.prowler.response import require_nonempty_string
from cartography.intel.prowler.response import require_object


def related_id(item: dict[str, Any], name: str, field: str) -> str | None:
    """Return the id of a to-one JSON:API relationship, or None when unset.

    Prowler renders an absent to-one relationship as `{"data": null}`, which is
    distinct from the relationship key being missing altogether.
    """
    relationships = item.get("relationships")
    if relationships is None:
        return None
    relationships = require_object(relationships, f"{field}.relationships")
    relationship = relationships.get(name)
    if relationship is None:
        return None
    relationship = require_object(relationship, f"{field}.relationships.{name}")
    data = relationship.get("data")
    if data is None:
        return None
    data = require_object(data, f"{field}.relationships.{name}.data")
    return require_nonempty_string(
        data.get("id"),
        f"{field}.relationships.{name}.data.id",
    )


def related_ids(item: dict[str, Any], name: str, field: str) -> list[str]:
    """Return the distinct ids of a to-many JSON:API relationship."""
    relationships = item.get("relationships")
    if relationships is None:
        return []
    relationships = require_object(relationships, f"{field}.relationships")
    relationship = relationships.get(name)
    if relationship is None:
        return []
    relationship = require_object(relationship, f"{field}.relationships.{name}")
    data = relationship.get("data")
    if data is None:
        return []
    entries = require_list(data, f"{field}.relationships.{name}.data")

    ids: list[str] = []
    for entry in entries:
        entry = require_object(entry, f"{field}.relationships.{name}.data item")
        identifier = require_nonempty_string(
            entry.get("id"),
            f"{field}.relationships.{name}.data item id",
        )
        if identifier not in ids:
            ids.append(identifier)
    return ids


def index_included(
    document: dict[str, Any],
    resource_type: str,
) -> dict[str, dict[str, Any]]:
    """Index a JSON:API document's sideloaded objects of one type by id.

    Sideloading with `include=` lets one request carry the related objects, so a
    transform can resolve relationships without an extra round trip per row.
    """
    included = document.get("included")
    if included is None:
        return {}
    entries = require_list(included, "Prowler included")

    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        entry = require_object(entry, "Prowler included item")
        if entry.get("type") != resource_type:
            continue
        identifier = require_nonempty_string(
            entry.get("id"),
            "Prowler included item id",
        )
        indexed[identifier] = entry
    return indexed
