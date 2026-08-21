from xml.etree import ElementTree

import pytest

from cartography.intel.openvas.hosts import _transform_host
from cartography.intel.openvas.hosts import transform_hosts
from tests.data.openvas.responses import GET_HOSTS_RESPONSE
from tests.data.openvas.responses import parse


def _assets() -> list:
    response = parse(GET_HOSTS_RESPONSE)
    return response.findall("asset")


def test_transform_host_uses_ip_identifier_as_id():
    asset = _assets()[0]
    transformed = _transform_host(asset)

    assert transformed["id"] == "10.0.0.5"
    assert transformed["ip"] == "10.0.0.5"
    assert transformed["hostname"] == "web-01.example.com"
    assert transformed["os"] == "Linux"
    assert transformed["severity"] == 8.1
    assert transformed["identifiers"] == "ip,hostname"


def test_transform_host_falls_back_to_name_when_no_ip_identifier():
    # Second fixture asset has an empty <identifiers/> block.
    asset = _assets()[1]
    transformed = _transform_host(asset)

    assert transformed["id"] == "10.0.0.6"
    assert transformed["hostname"] is None
    assert transformed["identifiers"] is None


def test_transform_host_missing_id_and_name_raises():
    asset = ElementTree.fromstring('<asset id="asset-1"><identifiers/></asset>')
    with pytest.raises(ValueError):
        _transform_host(asset)


def test_transform_hosts_transforms_all():
    hosts = transform_hosts(_assets())
    assert len(hosts) == 2
    assert {host["id"] for host in hosts} == {"10.0.0.5", "10.0.0.6"}
