from unittest.mock import MagicMock

import pytest

from cartography.intel.unifi import speedtests


class _FakeDevice:
    """Minimal stand-in for an aiounifi Device object backed by raw data."""

    def __init__(self, mac: str, raw: dict):
        self.mac = mac
        self.raw = raw

    @property
    def speedtest_status(self):
        return self.raw.get("speedtest-status")


@pytest.mark.asyncio
async def test_get_reads_speedtest_status_from_devices():
    """
    aiounifi has no dedicated speedtest handler; the controller only exposes
    the most recent speedtest run as a per-device raw field. get() must read
    it off controller.devices, skip devices with no speedtest data, and never
    call a nonexistent controller.speedtest attribute.
    """
    # Arrange
    gateway = _FakeDevice(
        "AA:BB:CC:DD:EE:FF",
        {
            "speedtest-status": {
                "latency": 15,
                "rundate": 1638342818,
                "xput_download": 100.5,
                "xput_upload": 20.2,
            },
        },
    )
    switch_without_speedtest = _FakeDevice("11:22:33:44:55:66", {})

    controller = MagicMock(spec=["devices"])
    controller.devices.values.return_value = [gateway, switch_without_speedtest]

    # Act
    result = await speedtests.get(controller, site_id="default")

    # Assert
    assert len(result) == 1
    assert result[0]["id"] == "default_AA:BB:CC:DD:EE:FF"
    assert result[0]["gateway_mac"] == "AA:BB:CC:DD:EE:FF"
    assert result[0]["download"] == 100.5
    assert result[0]["upload"] == 20.2
    assert result[0]["ping"] == 15
    assert result[0]["timestamp"] == 1638342818
