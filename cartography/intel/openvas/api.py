"""
GVM (Greenbone Management Protocol) connection and data-fetch helpers for the
OpenVAS intel module.

All fetching goes through python-gvm (https://github.com/greenbone/python-gvm)
using the Gmp protocol with the EtreeCheckCommandTransform, mirroring the
production deployment at
https://github.com/CyberSecAuto-Labs/OpenVAS-MCP (openvas_mcp/gvm_client.py).
"""

import logging
import socket
import ssl
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from datetime import UTC
from typing import Any
from typing import Optional

from gvm.connections import SSHConnection
from gvm.connections import TLSConnection
from gvm.connections import UnixSocketConnection
from gvm.connections._unix import AbstractGvmConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform

from cartography.config import Config

logger = logging.getLogger(__name__)

# Number of items fetched per page when paginating GMP list commands.
_PAGE_SIZE = 1000


class SocketConnection(AbstractGvmConnection):
    """
    Plain (non-TLS) TCP connection to a GVM socket proxy (e.g. socat).

    Upstream python-gvm only ships TLS and Unix socket connections; GVM itself
    does not expose plain TCP, but many deployments (including the one this
    module targets) front the gvmd protocol port with socat.
    """

    def __init__(
        self,
        hostname: str = "127.0.0.1",
        port: int = 9390,
        timeout: Optional[int] = 60,
    ) -> None:
        super().__init__(timeout=timeout)
        self.hostname = hostname
        self.port = port

    def connect(self) -> None:
        self._socket = socket.create_connection(
            (self.hostname, self.port),
            timeout=self._timeout,
        )


class VerifiedTLSConnection(TLSConnection):
    """
    TLS connection that verifies the server certificate by default.

    Upstream TLSConnection silently disables certificate verification when no
    cert files are provided (ssl.CERT_NONE + check_hostname=False). This
    subclass overrides _new_socket() to use ssl.create_default_context()
    (system CA bundle) unless an explicit CA file is provided.
    """

    def __init__(self, *, cafile: str = "", **kwargs: Any) -> None:
        super().__init__(cafile=cafile or None, **kwargs)
        self._cafile_override = cafile

    def _new_socket(self) -> ssl.SSLSocket:
        transport_socket = socket.create_connection(
            (self.hostname, self.port),
            timeout=self._timeout,
        )
        if self._cafile_override:
            # Self-signed GVM cert: verify against the provided CA file.
            context = ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH,
                cafile=self._cafile_override,
            )
        else:
            # Default: verify against the system CA bundle.
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        context.minimum_version = ssl.TLSVersion.TLSv1_2
        sock = context.wrap_socket(
            transport_socket,
            server_hostname=self.hostname,
        )
        sock.settimeout(self._timeout)
        return sock


def _make_connection(config: Config) -> Any:
    """
    Return a GVM connection based on the OpenVAS config options.

    - Unix socket when openvas_socket_path is set.
    - TLS when openvas_tls is set.
    - SSH when openvas_ssh is set.
    - Plain TCP socket proxy (socat) otherwise.
    """
    if config.openvas_socket_path:
        return UnixSocketConnection(path=config.openvas_socket_path)
    if config.openvas_ssh:
        return SSHConnection(
            hostname=config.openvas_host,
            port=config.openvas_port,
            username=config.openvas_user,
            password=config.openvas_password,
        )
    if config.openvas_tls:
        return VerifiedTLSConnection(
            hostname=config.openvas_host,
            port=config.openvas_port,
            cafile=config.openvas_tls_cafile or "",
        )
    logger.debug(
        "connecting to GVM over plain TCP — credentials will be sent "
        "unencrypted; set openvas_tls or openvas_socket_path for production",
    )
    return SocketConnection(
        hostname=config.openvas_host or "127.0.0.1",
        port=config.openvas_port,
    )


@contextmanager
def gmp_session(config: Config) -> Generator[Any, None, None]:
    """
    Yield an authenticated GMP session, closing it on exit.
    """
    connection = _make_connection(config)
    transform = EtreeCheckCommandTransform()
    with Gmp(connection=connection, transform=transform) as gmp:
        gmp.authenticate(config.openvas_user, config.openvas_password)
        yield gmp


def _text(element: Any, tag: str) -> Optional[str]:
    """
    Return the text of the first direct child with the given tag, or None.
    """
    child = element.find(tag)
    if child is None:
        return None
    value = child.text
    if value is None or value == "":
        return None
    return value.strip()


def _attr(element: Any, name: str) -> Optional[str]:
    """
    Return the given attribute of the element, or None.
    """
    value = element.get(name)
    if value is None or value == "":
        return None
    return value.strip()


def _children(element: Any, tag: str) -> list:
    """
    Return all direct children with the given tag.
    """
    return element.findall(tag)


_ITEMS_TAGS = {
    # get_hosts wraps GMP get_assets(type="host"); items and the count
    # element are keyed by "asset", not "host" (that's the nested detail
    # element inside each <asset>).
    "get_hosts": "asset",
    "get_tasks": "task",
    "get_results": "result",
    "get_tls_certificates": "tls_certificate",
    "get_targets": "target",
    "get_configs": "config",
    "get_schedules": "schedule",
    "get_port_lists": "port_list",
    "get_credentials": "credential",
}


def _fetch_all(
    gmp: Any,
    command: str,
    filter_string: Optional[str] = None,
    gmp_method: Optional[str] = None,
    extra_kwargs: Optional[dict] = None,
) -> list:
    """
    Fetch every page of a GMP list command, honoring its count tag.

    python-gvm's get_* methods don't take first/rows/ignore_pagination as
    separate arguments; GMP pagination is expressed inside filter_string
    (e.g. "first=1 rows=1000"), so page bounds are appended there.

    `command` keys `_ITEMS_TAGS` for the response element tag; `gmp_method`
    overrides the attribute called on `gmp` when it differs from `command`
    (e.g. get_configs -> gmp.get_scan_configs). `extra_kwargs` is passed
    through to the gmp method call (e.g. `details=True` for get_tasks, which
    GMP requires in order to include each task's `<last_report>` element).
    """
    all_items: list = []
    first = 1
    full_count: Optional[int] = None
    while True:
        logger.debug(
            "Fetching %s page %d..%d",
            command,
            first,
            first + _PAGE_SIZE - 1,
        )
        page_filter = f"first={first} rows={_PAGE_SIZE}"
        if filter_string:
            page_filter = f"{filter_string} {page_filter}"
        response = getattr(gmp, gmp_method or command)(
            filter_string=page_filter, **(extra_kwargs or {})
        )
        items = _children(response, _ITEMS_TAGS[command])
        all_items.extend(items)
        # List responses carry a <X_count> element. When no filter applies the
        # count covers all items; with a filter it carries full="1" when the
        # count covers every matching item and full="0" when it is truncated.
        count_elem = response.find(f"{_ITEMS_TAGS[command]}_count")
        if count_elem is not None and count_elem.get("full") != "0":
            try:
                full_count = int(count_elem.text or 0)
            except ValueError:
                full_count = None
        if not items or (full_count is not None and len(all_items) >= full_count):
            break
        first += _PAGE_SIZE
    logger.debug("Fetched %d items for %s", len(all_items), command)
    return all_items


def get_hosts(gmp: Any) -> list:
    return _fetch_all(gmp, "get_hosts")


def get_tasks(gmp: Any) -> list:
    # details=True is required for GMP to include each task's <last_report>
    # element (last_report_timestamp/scan_start/scan_end/severity); without
    # it, get_tasks only returns summary fields like creation_time and
    # modification_time, which reflect task config edits, not scan runs.
    return _fetch_all(gmp, "get_tasks", extra_kwargs={"details": True})


def get_results(gmp: Any, since: Optional[datetime] = None) -> list:
    filter_string = None
    if since is not None:
        filter_string = (
            f"created>{since.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )
    # details=True is required for GMP to include each result's <created> and
    # <task> elements; without it, get_results omits them, which is why
    # created/task_id/task_name previously loaded as null.
    return _fetch_all(
        gmp, "get_results", filter_string=filter_string, extra_kwargs={"details": True}
    )


def get_tls_certificates(gmp: Any) -> list:
    return _fetch_all(gmp, "get_tls_certificates")


def get_targets(gmp: Any) -> list:
    return _fetch_all(gmp, "get_targets")


def get_configs(gmp: Any) -> list:
    return _fetch_all(gmp, "get_configs", gmp_method="get_scan_configs")


def get_schedules(gmp: Any) -> list:
    return _fetch_all(gmp, "get_schedules")


def get_ports(gmp: Any) -> list:
    return _fetch_all(gmp, "get_port_lists")


def get_credentials(gmp: Any) -> list:
    return _fetch_all(gmp, "get_credentials")
