from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from cartography.intel.unifi import network_configs


@pytest.mark.asyncio
async def test_get_reads_rest_networkconf_endpoint():
    """
    aiounifi has no dedicated handler for network (VLAN) configs; get() must
    hit the raw /rest/networkconf endpoint via controller.request() rather
    than a nonexistent controller.object_oriented_network_configs attribute.
    """
    # Arrange
    controller = MagicMock(spec=["request"])
    controller.request = AsyncMock(
        return_value={
            "data": [
                {
                    "_id": "net_001",
                    "name": "Corporate LAN",
                    "enabled": True,
                    "purpose": "corporate",
                    "networkgroup": "LAN",
                    "domain_name": "lan",
                    "vlan_enabled": True,
                    "vlan": 10,
                    "ip_subnet": "10.0.10.1/24",
                    "is_guest": False,
                    "is_nat": True,
                    "attr_no_delete": True,
                    "dhcpd_enabled": True,
                    "dhcpd_start": "10.0.10.100",
                    "dhcpd_stop": "10.0.10.200",
                    "dhcpd_leasetime": 86400,
                    "dhcpd_dns_enabled": True,
                    "dhcpd_dns_1": "10.0.10.1",
                },
            ],
        }
    )

    # Act
    result = await network_configs.get(controller)

    # Assert
    assert len(result) == 1
    assert result[0]["id"] == "net_001"
    assert result[0]["purpose"] == "corporate"
    assert result[0]["vlan"] == 10
    assert result[0]["is_nat"] is True

    request_arg = controller.request.call_args[0][0]
    assert request_arg.method == "get"
    assert request_arg.path == "/rest/networkconf"


@pytest.mark.asyncio
async def test_get_handles_no_permission():
    """
    A controller account without access to network settings should not crash
    the sync -- get() should log a warning and return an empty list.
    """
    from aiounifi.errors import NoPermission

    # Arrange
    controller = MagicMock(spec=["request"])
    controller.request = AsyncMock(side_effect=NoPermission())

    # Act
    result = await network_configs.get(controller)

    # Assert
    assert result == []
