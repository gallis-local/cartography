import logging
import ssl

import aiohttp
from aiounifi.controller import Controller
from aiounifi.errors import AiounifiException
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
