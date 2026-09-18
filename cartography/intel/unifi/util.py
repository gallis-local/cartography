import logging
import ssl
from typing import Any

import aiohttp
from aiounifi.controller import Controller
from aiounifi.errors import AiounifiException
from aiounifi.errors import LoginRequired
from aiounifi.errors import NoPermission
from aiounifi.errors import Unauthorized
from aiounifi.models.configuration import Configuration

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each
_TIMEOUT = aiohttp.ClientTimeout(total=60)


async def create_unifi_controller(
    host: str,
    username: str,
    password: str,
    site: str = "default",
    port: int = 443,
    verify_ssl: bool = False,
) -> Controller:
    """
    Create and return a UniFi controller instance.

    :param host: UniFi controller host
    :param username: UniFi controller username
    :param password: UniFi controller password
    :param site: UniFi site name (default: 'default')
    :param port: UniFi controller port (default: 8443)
    :param verify_ssl: Whether to verify SSL certificates (default: False, as many UniFi controllers use self-signed certs)
    :return: Controller instance
    """
    # Create SSL context
    ssl_context = ssl.create_default_context()
    if not verify_ssl:
        # Disable SSL verification for self-signed certificates
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    # Create aiohttp session
    session = aiohttp.ClientSession(timeout=_TIMEOUT)

    # Create configuration
    config = Configuration(
        session=session,
        host=host,
        username=username,
        password=password,
        port=port,
        site=site,
        ssl_context=ssl_context,
    )

    # Create and login to controller
    controller = Controller(config)
    try:
        await controller.login()
    except (AiounifiException, aiohttp.ClientError):
        await session.close()
        raise

    return controller


async def close_controller(controller: Controller) -> None:
    """
    Close the UniFi controller connection and cleanup resources.

    :param controller: Controller instance to close
    """
    if controller and controller.connectivity.config.session:
        await controller.connectivity.config.session.close()


def to_float(value: Any) -> float | None:
    """
    Coerce a UniFi numeric telemetry field to a float.

    The controller reports power, voltage, current and power-factor readings as decimal
    strings ("117.257"). Storing them verbatim gives those graph properties a string type,
    so `o.power > 100` silently compares lexicographically and every consumer has to wrap
    the property in toFloat(). Returning None for an unparseable or absent reading keeps
    the property single-typed graph-wide rather than mixing numbers with sentinel strings.

    :param value: Raw value from the UniFi API
    :return: The value as a float, or None if it is absent or not numeric
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_permission_error(exception: Exception) -> bool:
    """
    Report whether a UniFi API exception was an authorization refusal.

    Callers that fetch the same optional resource once per site or per device use this to
    aggregate a single summary warning instead of emitting one per item.

    :param exception: Exception raised by a UniFi API call
    :return: True if the controller refused the call for lack of privilege
    """
    return isinstance(exception, (NoPermission, Unauthorized))


def log_optional_fetch_failure(
    exception: Exception,
    description: str,
    **context: Any,
) -> None:
    """
    Log a failed best-effort UniFi fetch at a level that reflects its cause.

    These fetches return an empty list on failure so one missing privilege or one endpoint
    absent from an older controller does not abort the whole sync. The danger is that "the
    controller refused us" and "there is genuinely nothing here" then look identical in the
    graph: both produce zero nodes. Logging an authorization problem at WARNING and naming
    the privilege keeps that distinction visible, because a silently incomplete graph is
    worse than a loud failure -- an operator who sees zero UnifiAdmin nodes needs to know
    whether that means "no admins exist" or "we were not allowed to look".

    :param exception: Exception raised by the UniFi API call
    :param description: Human-readable description of what was being fetched
    :param context: Extra key/value pairs to include in the log message
    """
    suffix = "".join(f" ({k}={v})" for k, v in context.items())

    if is_permission_error(exception):
        logger.warning(
            "Permission denied fetching %s%s: %s. The UniFi service account is missing a "
            "required privilege, so this data will be ABSENT from the graph rather than "
            "empty. Grant the privilege to avoid silently incomplete results.",
            description,
            suffix,
            exception,
        )
    elif isinstance(exception, LoginRequired):
        logger.warning(
            "Session expired or credentials rejected while fetching %s%s: %s. Check that "
            "the UniFi service account credentials are valid.",
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


def scoped_id(site_id: str, value: str | None) -> str | None:
    """
    Build a site-scoped node id from a controller-local identifier.

    MAC addresses are only unique within one controller. Keying UnifiClient and UnifiDevice
    on the bare MAC meant the same physical machine seen by two controllers collapsed onto a
    single node that carried RESOURCE edges from both sites and a site_id that flip-flopped
    depending on which sync ran last. Prefixing the site keeps the two observations distinct.

    :param site_id: Id of the UnifiSite the identifier belongs to
    :param value: Controller-local identifier, typically a MAC address
    :return: The site-scoped id, or None if there was no identifier to scope
    """
    return f"{site_id}_{value}" if value else None


def scoped_ids(site_id: str, values: list[str] | None) -> list[str] | None:
    """
    Build site-scoped node ids for a list of controller-local identifiers.

    Used by the rules and policies that reference clients by MAC through a one_to_many
    matcher. Empty entries are dropped rather than scoped into an id that matches nothing.

    :param site_id: Id of the UnifiSite the identifiers belong to
    :param values: Controller-local identifiers, typically MAC addresses
    :return: The site-scoped ids, or None if there were none to scope
    """
    if not values:
        return None
    return [f"{site_id}_{value}" for value in values if value]


def attach_scoped_ids(
    rows: list[dict[str, Any]],
    site_id: str,
    single: dict[str, str] | None = None,
    multiple: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Return copies of rows carrying site-scoped ids derived from their MAC-valued fields.

    The raw MAC fields are kept: they are useful data in their own right, and several node
    schemas expose them as properties. Only the derived ``*_id`` fields are what the node
    identity and the relationship matchers resolve on.

    :param rows: Rows about to be loaded
    :param site_id: Id of the UnifiSite being synced
    :param single: Mapping of derived id field name to the single-MAC field it scopes
    :param multiple: Mapping of derived id field name to the MAC-list field it scopes
    :return: New rows with the derived id fields added
    """
    scoped_rows = []
    for row in rows:
        scoped = dict(row)
        for id_field, mac_field in (single or {}).items():
            scoped[id_field] = scoped_id(site_id, row.get(mac_field))
        for id_field, mac_field in (multiple or {}).items():
            scoped[id_field] = scoped_ids(site_id, row.get(mac_field))
        scoped_rows.append(scoped)
    return scoped_rows
