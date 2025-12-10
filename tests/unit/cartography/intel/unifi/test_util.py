from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.unifi.util import get_unifi_client


@patch("cartography.intel.unifi.util.UnifiClient")
def test_get_unifi_client(mock_unifi_client_class):
    """
    Test that get_unifi_client creates a UnifiClient with correct parameters.
    """
    # Arrange
    mock_client_instance = MagicMock()
    mock_unifi_client_class.return_value = mock_client_instance

    host = "192.168.1.1"
    username = "admin"
    password = "testpassword"
    site = "default"

    # Act
    result = get_unifi_client(host, username, password, site)

    # Assert
    mock_unifi_client_class.assert_called_once_with(
        host=host,
        username=username,
        password=password,
        site=site,
    )
    assert result == mock_client_instance


@patch("cartography.intel.unifi.util.UnifiClient")
def test_get_unifi_client_custom_site(mock_unifi_client_class):
    """
    Test that get_unifi_client works with a custom site name.
    """
    # Arrange
    mock_client_instance = MagicMock()
    mock_unifi_client_class.return_value = mock_client_instance

    host = "unifi.example.com"
    username = "admin"
    password = "secretpassword"
    site = "office-site"

    # Act
    result = get_unifi_client(host, username, password, site)

    # Assert
    mock_unifi_client_class.assert_called_once_with(
        host=host,
        username=username,
        password=password,
        site=site,
    )
    assert result == mock_client_instance
