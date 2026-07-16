from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from cartography.intel.unifi import port_forwards


class _FakePortForward:
    """Minimal stand-in for an aiounifi PortForward object backed by raw data."""

    def __init__(self, raw: dict):
        self.raw = raw

    @property
    def id(self) -> str:
        return self.raw["_id"]

    @property
    def name(self) -> str:
        return self.raw["name"]

    @property
    def enabled(self) -> bool:
        return self.raw.get("enabled", False)

    @property
    def destination_port(self) -> str:
        return self.raw["dst_port"]

    @property
    def forward_port(self) -> str:
        return self.raw["fwd_port"]

    @property
    def forward_ip(self) -> str:
        return self.raw["fwd"]

    @property
    def protocol(self) -> str:
        return self.raw["proto"]

    @property
    def port_forward_interface(self) -> str:
        return self.raw["pfwd_interface"]


@pytest.mark.asyncio
async def test_get_handles_missing_src():
    """
    Some UniFi controller firmware returns port-forward objects without the
    `src` key that aiounifi's `PortForward.source` property requires. `get()`
    must not crash on such objects and should capture `source` as None.
    """
    # Arrange
    pf_with_src = _FakePortForward(
        {
            "_id": "pf_001",
            "name": "Web Server",
            "enabled": True,
            "dst_port": "80",
            "fwd_port": "8080",
            "fwd": "192.168.1.50",
            "proto": "tcp",
            "pfwd_interface": "wan",
            "src": "any",
        }
    )
    pf_without_src = _FakePortForward(
        {
            "_id": "pf_002",
            "name": "SSH Server",
            "enabled": False,
            "dst_port": "22",
            "fwd_port": "22",
            "fwd": "192.168.1.51",
            "proto": "tcp",
            "pfwd_interface": "wan",
        }
    )

    collection = MagicMock()
    collection.update = AsyncMock()
    collection.values.return_value = [pf_with_src, pf_without_src]

    controller = MagicMock()
    controller.port_forwarding = collection

    # Act
    result = await port_forwards.get(controller)

    # Assert
    assert {r["id"] for r in result} == {"pf_001", "pf_002"}
    assert result[0]["source"] == "any"
    assert result[1]["source"] is None
