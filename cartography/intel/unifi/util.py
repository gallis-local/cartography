import logging

from unificontrol import UnifiClient

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each
_TIMEOUT = (60, 60)


def get_unifi_client(host: str, username: str, password: str, site: str) -> UnifiClient:
    """
    Create and return a UniFi client instance.

    :param host: UniFi controller host
    :param username: UniFi controller username
    :param password: UniFi controller password
    :param site: UniFi site name
    :return: UnifiClient instance
    """
    return UnifiClient(host=host, username=username, password=password, site=site)
