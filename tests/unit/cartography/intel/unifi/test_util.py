from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.unifi.util import close_controller
from cartography.intel.unifi.util import create_unifi_controller


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
    mock_controller.connectivity.session = mock_session

    # Act
    await close_controller(mock_controller)

    # Assert
    mock_session.close.assert_called_once()
