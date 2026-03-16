"""
Integration tests for Proxmox SDN (Software-Defined Networking) sync.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import pytest

from cartography.intel.proxmox import sdn
CLUSTER_ID = "test-cluster"


@pytest.fixture
def proxmox_client_mock():
    """Create a mock Proxmox client with SDN API methods."""
    mock_client = MagicMock()

    # Mock SDN zones API
    mock_client.cluster.sdn.zones.get.return_value = [
        {
            "zone": "zone1",
            "type": "vlan",
            "bridge": "vmbr0",
            "nodes": "node1,node2",
            "mtu": "1500",
        },
        {
            "zone": "zone2",
            "type": "vxlan",
            "bridge": "vmbr1",
            "peers": "192.168.1.1,192.168.1.2",
            "controller": "evpn1",
        },
    ]

    # Mock SDN VNets API
    mock_client.cluster.sdn.vnets.get.return_value = [
        {
            "vnet": "vnet100",
            "zone": "zone1",
            "tag": "100",
            "alias": "DMZ Network",
            "vlanaware": 1,
        },
        {
            "vnet": "vnet200",
            "zone": "zone2",
            "alias": "Internal Network",
        },
    ]

    # Mock SDN subnets API for vnet100
    mock_vnets = MagicMock()
    mock_vnet100 = MagicMock()
    mock_vnet100.subnets.get.return_value = [
        {
            "subnet": "10.0.1.0/24",
            "gateway": "10.0.1.1",
            "snat": 1,
            "dhcp-range": "10.0.1.100-10.0.1.200",
        },
        {
            "subnet": "10.0.2.0/24",
            "gateway": "10.0.2.1",
        },
    ]
    mock_vnets.return_value = mock_vnet100

    # Mock SDN subnets API for vnet200
    mock_vnet200 = MagicMock()
    mock_vnet200.subnets.get.return_value = [
        {
            "subnet": "192.168.1.0/24",
            "gateway": "192.168.1.1",
        },
    ]

    # Configure vnets to return appropriate subnet mock based on vnet_id
    def get_vnet_mock(vnet_id):
        if vnet_id == "vnet100":
            return mock_vnet100
        elif vnet_id == "vnet200":
            return mock_vnet200
        return MagicMock()

    mock_client.cluster.sdn.vnets.side_effect = get_vnet_mock

    # Mock SDN controllers API
    mock_client.cluster.sdn.controllers.get.return_value = [
        {
            "controller": "evpn1",
            "type": "evpn",
            "asn": "65000",
            "peers": "192.168.1.1,192.168.1.2,192.168.1.3",
            "node": "node1",
        },
    ]

    # Mock SDN IPAMs API
    mock_client.cluster.sdn.ipams.get.return_value = [
        {
            "ipam": "pve",
            "type": "pve",
        },
        {
            "ipam": "netbox1",
            "type": "netbox",
            "url": "https://netbox.example.com",
            "token": "secret-token",
            "section": "1",
        },
    ]

    return mock_client


def test_sdn_zones_transform():
    """Test transforming SDN zone data."""
    zones_data = [
        {
            "zone": "zone1",
            "type": "vlan",
            "bridge": "vmbr0",
            "mtu": "1500",
        },
    ]

    zones = sdn.transform_sdn_zones(zones_data, CLUSTER_ID)

    assert len(zones) == 1
    assert zones[0]["id"] == f"{CLUSTER_ID}/sdn/zone/zone1"
    assert zones[0]["zone"] == "zone1"
    assert zones[0]["type"] == "vlan"
    assert zones[0]["bridge"] == "vmbr0"
    assert zones[0]["cluster_id"] == CLUSTER_ID


def test_sdn_vnets_transform():
    """Test transforming SDN VNet data."""
    vnets_data = [
        {
            "vnet": "vnet100",
            "zone": "zone1",
            "tag": "100",
            "alias": "DMZ Network",
        },
    ]

    vnets = sdn.transform_sdn_vnets(vnets_data, CLUSTER_ID)

    assert len(vnets) == 1
    assert vnets[0]["id"] == f"{CLUSTER_ID}/sdn/vnet/vnet100"
    assert vnets[0]["vnet"] == "vnet100"
    assert vnets[0]["zone"] == "zone1"
    assert vnets[0]["tag"] == "100"
    assert vnets[0]["cluster_id"] == CLUSTER_ID


def test_sdn_subnets_transform():
    """Test transforming SDN subnet data."""
    subnets_data = [
        {
            "subnet": "10.0.1.0/24",
            "gateway": "10.0.1.1",
            "snat": 1,
        },
    ]

    subnets = sdn.transform_sdn_subnets(subnets_data, "vnet100", CLUSTER_ID)

    assert len(subnets) == 1
    # Subnet CIDR in ID should have / replaced with _
    assert subnets[0]["id"] == f"{CLUSTER_ID}/sdn/vnet/vnet100/subnet/10.0.1.0_24"
    assert subnets[0]["subnet"] == "10.0.1.0/24"
    assert subnets[0]["vnet"] == "vnet100"
    assert subnets[0]["gateway"] == "10.0.1.1"
    assert subnets[0]["cluster_id"] == CLUSTER_ID


def test_sdn_controllers_transform():
    """Test transforming SDN controller data."""
    controllers_data = [
        {
            "controller": "evpn1",
            "type": "evpn",
            "asn": "65000",
            "peers": "192.168.1.1,192.168.1.2",
        },
    ]

    controllers = sdn.transform_sdn_controllers(controllers_data, CLUSTER_ID)

    assert len(controllers) == 1
    assert controllers[0]["id"] == f"{CLUSTER_ID}/sdn/controller/evpn1"
    assert controllers[0]["controller"] == "evpn1"
    assert controllers[0]["type"] == "evpn"
    assert controllers[0]["asn"] == "65000"
    assert controllers[0]["cluster_id"] == CLUSTER_ID


def test_sdn_ipams_transform():
    """Test transforming SDN IPAM data."""
    ipams_data = [
        {
            "ipam": "netbox1",
            "type": "netbox",
            "url": "https://netbox.example.com",
            "token": "secret-token",
        },
    ]

    ipams = sdn.transform_sdn_ipams(ipams_data, CLUSTER_ID)

    assert len(ipams) == 1
    assert ipams[0]["id"] == f"{CLUSTER_ID}/sdn/ipam/netbox1"
    assert ipams[0]["ipam"] == "netbox1"
    assert ipams[0]["type"] == "netbox"
    assert ipams[0]["token"] == "configured"  # Should mask actual token
    assert ipams[0]["cluster_id"] == CLUSTER_ID


def test_sync_sdn_zones(neo4j_session: neo4j.Session, proxmox_client_mock):
    """Test syncing SDN zones to Neo4j."""
    update_tag = 12345

    sdn.sync_sdn(
        neo4j_session,
        proxmox_client_mock,
        CLUSTER_ID,
        update_tag,
    )

    # Verify zones were created
    result = neo4j_session.run(
        """
        MATCH (z:ProxmoxSDNZone{id: $zone_id})
        RETURN z.zone as zone, z.type as type, z.bridge as bridge
        """,
        zone_id=f"{CLUSTER_ID}/sdn/zone/zone1",
    )
    record = result.single()
    assert record is not None
    assert record["zone"] == "zone1"
    assert record["type"] == "vlan"
    assert record["bridge"] == "vmbr0"

    # Verify zone relationship to cluster
    result = neo4j_session.run(
        """
        MATCH (z:ProxmoxSDNZone{id: $zone_id})-[:RESOURCE]->(c:ProxmoxCluster{id: $cluster_id})
        RETURN count(z) as count
        """,
        zone_id=f"{CLUSTER_ID}/sdn/zone/zone1",
        cluster_id=CLUSTER_ID,
    )
    assert result.single()["count"] == 1


def test_sync_sdn_vnets(neo4j_session: neo4j.Session, proxmox_client_mock):
    """Test syncing SDN VNets to Neo4j."""
    update_tag = 12345

    sdn.sync_sdn(
        neo4j_session,
        proxmox_client_mock,
        CLUSTER_ID,
        update_tag,
    )

    # Verify VNet was created
    result = neo4j_session.run(
        """
        MATCH (v:ProxmoxSDNVNet{id: $vnet_id})
        RETURN v.vnet as vnet, v.zone as zone, v.alias as alias
        """,
        vnet_id=f"{CLUSTER_ID}/sdn/vnet/vnet100",
    )
    record = result.single()
    assert record is not None
    assert record["vnet"] == "vnet100"
    assert record["zone"] == "zone1"
    assert record["alias"] == "DMZ Network"

    # Verify VNet belongs to zone
    result = neo4j_session.run(
        """
        MATCH (v:ProxmoxSDNVNet{id: $vnet_id})-[:BELONGS_TO]->(z:ProxmoxSDNZone)
        RETURN z.zone as zone
        """,
        vnet_id=f"{CLUSTER_ID}/sdn/vnet/vnet100",
    )
    record = result.single()
    assert record is not None
    assert record["zone"] == "zone1"


def test_sync_sdn_subnets(neo4j_session: neo4j.Session, proxmox_client_mock):
    """Test syncing SDN subnets to Neo4j."""
    update_tag = 12345

    sdn.sync_sdn(
        neo4j_session,
        proxmox_client_mock,
        CLUSTER_ID,
        update_tag,
    )

    # Verify subnet was created
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxSDNSubnet)
        WHERE s.subnet = $subnet
        RETURN s.id as id, s.vnet as vnet, s.gateway as gateway, s.snat as snat
        """,
        subnet="10.0.1.0/24",
    )
    record = result.single()
    assert record is not None
    assert record["id"] == f"{CLUSTER_ID}/sdn/vnet/vnet100/subnet/10.0.1.0_24"
    assert record["vnet"] == "vnet100"
    assert record["gateway"] == "10.0.1.1"
    assert record["snat"] == 1

    # Verify subnet belongs to VNet
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxSDNSubnet{subnet: $subnet})-[:BELONGS_TO]->(v:ProxmoxSDNVNet)
        RETURN v.vnet as vnet
        """,
        subnet="10.0.1.0/24",
    )
    record = result.single()
    assert record is not None
    assert record["vnet"] == "vnet100"


def test_sync_sdn_controllers(neo4j_session: neo4j.Session, proxmox_client_mock):
    """Test syncing SDN controllers to Neo4j."""
    update_tag = 12345

    sdn.sync_sdn(
        neo4j_session,
        proxmox_client_mock,
        CLUSTER_ID,
        update_tag,
    )

    # Verify controller was created
    result = neo4j_session.run(
        """
        MATCH (c:ProxmoxSDNController{id: $controller_id})
        RETURN c.controller as controller, c.type as type, c.asn as asn
        """,
        controller_id=f"{CLUSTER_ID}/sdn/controller/evpn1",
    )
    record = result.single()
    assert record is not None
    assert record["controller"] == "evpn1"
    assert record["type"] == "evpn"
    assert record["asn"] == "65000"


def test_sync_sdn_ipams(neo4j_session: neo4j.Session, proxmox_client_mock):
    """Test syncing SDN IPAMs to Neo4j."""
    update_tag = 12345

    sdn.sync_sdn(
        neo4j_session,
        proxmox_client_mock,
        CLUSTER_ID,
        update_tag,
    )

    # Verify IPAM was created
    result = neo4j_session.run(
        """
        MATCH (i:ProxmoxSDNIPAM{id: $ipam_id})
        RETURN i.ipam as ipam, i.type as type, i.token as token
        """,
        ipam_id=f"{CLUSTER_ID}/sdn/ipam/netbox1",
    )
    record = result.single()
    assert record is not None
    assert record["ipam"] == "netbox1"
    assert record["type"] == "netbox"
    assert record["token"] == "configured"  # Should mask actual token


def test_sdn_api_error_handling(neo4j_session: neo4j.Session):
    """Test handling of API errors during SDN sync."""
    mock_client = MagicMock()

    # Simulate API errors
    mock_client.cluster.sdn.zones.get.side_effect = Exception("API Error")
    mock_client.cluster.sdn.vnets.get.side_effect = Exception("API Error")
    mock_client.cluster.sdn.controllers.get.side_effect = Exception("API Error")
    mock_client.cluster.sdn.ipams.get.side_effect = Exception("API Error")

    update_tag = 12345

    # Should not raise exception
    sdn.sync_sdn(
        neo4j_session,
        mock_client,
        CLUSTER_ID,
        update_tag,
    )

    # No SDN resources should be created
    result = neo4j_session.run("MATCH (z:ProxmoxSDNZone) RETURN count(z) as count")
    assert result.single()["count"] == 0
