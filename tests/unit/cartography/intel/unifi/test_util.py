import logging
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from aiounifi.errors import AiounifiException
from aiounifi.errors import LoginRequired
from aiounifi.errors import NoPermission
from aiounifi.errors import Unauthorized

from cartography.intel.unifi.util import close_controller
from cartography.intel.unifi.util import create_unifi_controller
from cartography.intel.unifi.util import is_permission_error
from cartography.intel.unifi.util import log_optional_fetch_failure
from cartography.intel.unifi.util import to_float


@pytest.mark.asyncio
@patch("cartography.intel.unifi.util.Controller")
@patch("cartography.intel.unifi.util.aiohttp.ClientSession")
async def test_create_unifi_controller(mock_session_class, mock_controller_class):
    """
    Test that create_unifi_controller creates a Controller with correct parameters.
    """
    # Arrange
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_controller = MagicMock()
    mock_controller.login = AsyncMock()
    mock_controller_class.return_value = mock_controller

    host = "192.168.1.1"
    username = "admin"
    password = "testpassword"
    site = "default"
    port = 8443

    # Act
    result = await create_unifi_controller(host, username, password, site, port)

    # Assert
    mock_session_class.assert_called_once()
    mock_controller_class.assert_called_once()
    mock_controller.login.assert_called_once()
    assert result == mock_controller


@pytest.mark.asyncio
@patch("cartography.intel.unifi.util.Controller")
@patch("cartography.intel.unifi.util.aiohttp.ClientSession")
async def test_create_unifi_controller_custom_site(
    mock_session_class, mock_controller_class
):
    """
    Test that create_unifi_controller works with a custom site name.
    """
    # Arrange
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_controller = MagicMock()
    mock_controller.login = AsyncMock()
    mock_controller_class.return_value = mock_controller

    host = "unifi.example.com"
    username = "admin"
    password = "secretpassword"
    site = "office-site"
    port = 8443

    # Act
    result = await create_unifi_controller(host, username, password, site, port)

    # Assert
    mock_controller_class.assert_called_once()
    mock_controller.login.assert_called_once()
    assert result == mock_controller


@pytest.mark.asyncio
async def test_close_controller():
    """
    Test that close_controller properly closes the session.
    """
    # Arrange
    mock_session = MagicMock()
    mock_session.close = AsyncMock()

    mock_controller = MagicMock()
    mock_controller.connectivity = MagicMock()
    mock_controller.connectivity.config = MagicMock()
    mock_controller.connectivity.config.session = mock_session

    # Act
    await close_controller(mock_controller)

    # Assert
    mock_session.close.assert_called_once()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("117.257", 117.257),
        ("0.000", 0.0),
        (5, 5.0),
        (None, None),
        ("", None),
        ("unknown", None),
        (True, None),
    ],
)
def test_to_float(raw, expected):
    """
    The controller reports power telemetry as decimal strings, and absent or unparseable
    readings must become None rather than a sentinel so the graph property stays one type.
    """
    assert to_float(raw) == expected


def test_is_permission_error_distinguishes_authorization_from_other_failures():
    """
    Permission refusals are aggregated into one summary warning by per-item callers, so
    they must be distinguishable from an expired session or a generic API error.
    """
    assert is_permission_error(NoPermission()) is True
    assert is_permission_error(Unauthorized()) is True
    assert is_permission_error(LoginRequired()) is False
    assert is_permission_error(AiounifiException()) is False


def test_log_optional_fetch_failure_warns_on_permission_denial(caplog):
    """
    A permission denial yields zero nodes just like "no data exists", so it must be logged
    loudly enough that an operator does not read an empty graph as a complete one.
    """
    with caplog.at_level(logging.WARNING, logger="cartography.intel.unifi.util"):
        log_optional_fetch_failure(NoPermission(), "UniFi admins", site="default")

    assert "Permission denied fetching UniFi admins (site=default)" in caplog.text
    assert "ABSENT from the graph" in caplog.text


def test_log_optional_fetch_failure_warns_on_generic_error(caplog):
    """
    An unexpected API error also silently empties the graph, so it stays at WARNING.
    """
    with caplog.at_level(logging.WARNING, logger="cartography.intel.unifi.util"):
        log_optional_fetch_failure(AiounifiException("boom"), "UniFi vouchers")

    assert "Could not fetch UniFi vouchers" in caplog.text
