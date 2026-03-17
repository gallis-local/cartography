"""
Sync Proxmox SDN (Software-Defined Networking) resources.

This module handles synchronization of SDN zones, VNets, subnets,
controllers, and IPAM configurations.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.models.proxmox.sdn import ProxmoxSDNControllerSchema
from cartography.models.proxmox.sdn import ProxmoxSDNIPAMSchema
from cartography.models.proxmox.sdn import ProxmoxSDNSubnetSchema
from cartography.models.proxmox.sdn import ProxmoxSDNVNetSchema
from cartography.models.proxmox.sdn import ProxmoxSDNZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_sdn_zones(proxmox_client: Any) -> List[Dict[str, Any]]:
    """
    Get all SDN zones from the cluster.

    :param proxmox_client: Proxmoxer API client
    :return: List of zone data dictionaries
    """
    try:
        return proxmox_client.cluster.sdn.zones.get()
    except Exception as e:
        logger.warning(f"Failed to get SDN zones: {e}")
        return []


@timeit
def get_sdn_vnets(proxmox_client: Any) -> List[Dict[str, Any]]:
    """
    Get all SDN VNets from the cluster.

    :param proxmox_client: Proxmoxer API client
    :return: List of VNet data dictionaries
    """
    try:
        return proxmox_client.cluster.sdn.vnets.get()
    except Exception as e:
        logger.warning(f"Failed to get SDN VNets: {e}")
        return []


@timeit
def get_sdn_subnets(proxmox_client: Any, vnet: str) -> List[Dict[str, Any]]:
    """
    Get all subnets for a specific VNet.

    :param proxmox_client: Proxmoxer API client
    :param vnet: VNet ID
    :return: List of subnet data dictionaries
    """
    try:
        return proxmox_client.cluster.sdn.vnets(vnet).subnets.get()
    except Exception as e:
        logger.debug(f"No subnets found for VNet {vnet}: {e}")
        return []


@timeit
def get_sdn_controllers(proxmox_client: Any) -> List[Dict[str, Any]]:
    """
    Get all SDN controllers from the cluster.

    :param proxmox_client: Proxmoxer API client
    :return: List of controller data dictionaries
    """
    try:
        return proxmox_client.cluster.sdn.controllers.get()
    except Exception as e:
        logger.warning(f"Failed to get SDN controllers: {e}")
        return []


@timeit
def get_sdn_ipams(proxmox_client: Any) -> List[Dict[str, Any]]:
    """
    Get all SDN IPAM configurations from the cluster.

    :param proxmox_client: Proxmoxer API client
    :return: List of IPAM data dictionaries
    """
    try:
        return proxmox_client.cluster.sdn.ipams.get()
    except Exception as e:
        logger.warning(f"Failed to get SDN IPAMs: {e}")
        return []


@timeit
def transform_sdn_zones(
    zones_data: List[Dict[str, Any]], cluster_id: str
) -> List[Dict[str, Any]]:
    """
    Transform SDN zone data to match ProxmoxSDNZoneSchema.

    :param zones_data: Raw zone data from API
    :param cluster_id: Cluster identifier
    :return: Transformed zone data
    """
    transformed_zones = []
    for zone in zones_data:
        zone_id = zone.get("zone")
        if not zone_id:
            continue

        transformed_zones.append(
            {
                "id": f"{cluster_id}/sdn/zone/{zone_id}",
                "zone": zone_id,
                "type": zone.get("type"),
                "cluster_id": cluster_id,
                "bridge": zone.get("bridge"),
                "nodes": zone.get("nodes"),
                "mtu": zone.get("mtu"),
                "tag": zone.get("tag"),
                "peers": zone.get("peers"),
                "controller": zone.get("controller"),
                "ipam": zone.get("ipam"),
                "dns": zone.get("dns"),
                "reversedns": zone.get("reversedns"),
                "dnszone": zone.get("dnszone"),
                "vrf_vxlan": zone.get("vrf-vxlan"),
                "vxlan_port": zone.get("vxlan-port"),
                "mac": zone.get("mac"),
                "service_vlan": zone.get("service-vlan"),
            }
        )
    return transformed_zones


@timeit
def transform_sdn_vnets(
    vnets_data: List[Dict[str, Any]], cluster_id: str
) -> List[Dict[str, Any]]:
    """
    Transform SDN VNet data to match ProxmoxSDNVNetSchema.

    :param vnets_data: Raw VNet data from API
    :param cluster_id: Cluster identifier
    :return: Transformed VNet data
    """
    transformed_vnets = []
    for vnet in vnets_data:
        vnet_id = vnet.get("vnet")
        if not vnet_id:
            continue

        transformed_vnets.append(
            {
                "id": f"{cluster_id}/sdn/vnet/{vnet_id}",
                "vnet": vnet_id,
                "zone": vnet.get("zone"),
                "cluster_id": cluster_id,
                "tag": vnet.get("tag"),
                "alias": vnet.get("alias"),
                "vlanaware": vnet.get("vlanaware"),
                "mac": vnet.get("mac"),
            }
        )
    return transformed_vnets


@timeit
def transform_sdn_subnets(
    subnets_data: List[Dict[str, Any]], vnet_id: str, cluster_id: str
) -> List[Dict[str, Any]]:
    """
    Transform SDN subnet data to match ProxmoxSDNSubnetSchema.

    :param subnets_data: Raw subnet data from API
    :param vnet_id: Parent VNet ID (not full path, just the ID)
    :param cluster_id: Cluster identifier
    :return: Transformed subnet data
    """
    transformed_subnets = []
    for subnet in subnets_data:
        subnet_cidr = subnet.get("subnet")
        if not subnet_cidr:
            continue

        # Use URL-safe subnet ID (replace / with _)
        subnet_safe_id = subnet_cidr.replace("/", "_")

        transformed_subnets.append(
            {
                "id": f"{cluster_id}/sdn/vnet/{vnet_id}/subnet/{subnet_safe_id}",
                "subnet": subnet_cidr,
                "vnet": vnet_id,
                "cluster_id": cluster_id,
                "gateway": subnet.get("gateway"),
                "snat": subnet.get("snat"),
                "dhcp_range": subnet.get("dhcp-range"),
                "dnszoneprefix": subnet.get("dnszoneprefix"),
            }
        )
    return transformed_subnets


@timeit
def transform_sdn_controllers(
    controllers_data: List[Dict[str, Any]], cluster_id: str
) -> List[Dict[str, Any]]:
    """
    Transform SDN controller data to match ProxmoxSDNControllerSchema.

    :param controllers_data: Raw controller data from API
    :param cluster_id: Cluster identifier
    :return: Transformed controller data
    """
    transformed_controllers = []
    for controller in controllers_data:
        controller_id = controller.get("controller")
        if not controller_id:
            continue

        transformed_controllers.append(
            {
                "id": f"{cluster_id}/sdn/controller/{controller_id}",
                "controller": controller_id,
                "type": controller.get("type"),
                "cluster_id": cluster_id,
                "asn": controller.get("asn"),
                "peers": controller.get("peers"),
                "node": controller.get("node"),
                "ebgp": controller.get("ebgp"),
                "loopback": controller.get("loopback"),
                "bgp_multipath_as_path_relax": controller.get("bgp-multipath-as-path-relax"),
            }
        )
    return transformed_controllers


@timeit
def transform_sdn_ipams(
    ipams_data: List[Dict[str, Any]], cluster_id: str
) -> List[Dict[str, Any]]:
    """
    Transform SDN IPAM data to match ProxmoxSDNIPAMSchema.

    :param ipams_data: Raw IPAM data from API
    :param cluster_id: Cluster identifier
    :return: Transformed IPAM data
    """
    transformed_ipams = []
    for ipam in ipams_data:
        ipam_id = ipam.get("ipam")
        if not ipam_id:
            continue

        transformed_ipams.append(
            {
                "id": f"{cluster_id}/sdn/ipam/{ipam_id}",
                "ipam": ipam_id,
                "type": ipam.get("type"),
                "cluster_id": cluster_id,
                "url": ipam.get("url"),
                "section": ipam.get("section"),
            }
        )
    return transformed_ipams


@timeit
def load_sdn_zones(
    neo4j_session: neo4j.Session,
    zones: List[Dict[str, Any]],
    cluster_id: str,
    proxmox_update_tag: int,
) -> None:
    """
    Load SDN zones into Neo4j.

    :param neo4j_session: Neo4j session
    :param zones: Transformed zone data
    :param cluster_id: Cluster identifier
    :param proxmox_update_tag: Update tag for cleanup
    """
    load(
        neo4j_session,
        ProxmoxSDNZoneSchema(),
        zones,
        lastupdated=proxmox_update_tag,
        CLUSTER_ID=cluster_id,
    )


@timeit
def load_sdn_vnets(
    neo4j_session: neo4j.Session,
    vnets: List[Dict[str, Any]],
    cluster_id: str,
    proxmox_update_tag: int,
) -> None:
    """
    Load SDN VNets into Neo4j.

    :param neo4j_session: Neo4j session
    :param vnets: Transformed VNet data
    :param cluster_id: Cluster identifier
    :param proxmox_update_tag: Update tag for cleanup
    """
    load(
        neo4j_session,
        ProxmoxSDNVNetSchema(),
        vnets,
        lastupdated=proxmox_update_tag,
        CLUSTER_ID=cluster_id,
    )


@timeit
def load_sdn_subnets(
    neo4j_session: neo4j.Session,
    subnets: List[Dict[str, Any]],
    cluster_id: str,
    proxmox_update_tag: int,
) -> None:
    """
    Load SDN subnets into Neo4j.

    :param neo4j_session: Neo4j session
    :param subnets: Transformed subnet data
    :param cluster_id: Cluster identifier
    :param proxmox_update_tag: Update tag for cleanup
    """
    load(
        neo4j_session,
        ProxmoxSDNSubnetSchema(),
        subnets,
        lastupdated=proxmox_update_tag,
        CLUSTER_ID=cluster_id,
    )


@timeit
def load_sdn_controllers(
    neo4j_session: neo4j.Session,
    controllers: List[Dict[str, Any]],
    cluster_id: str,
    proxmox_update_tag: int,
) -> None:
    """
    Load SDN controllers into Neo4j.

    :param neo4j_session: Neo4j session
    :param controllers: Transformed controller data
    :param cluster_id: Cluster identifier
    :param proxmox_update_tag: Update tag for cleanup
    """
    load(
        neo4j_session,
        ProxmoxSDNControllerSchema(),
        controllers,
        lastupdated=proxmox_update_tag,
        CLUSTER_ID=cluster_id,
    )


@timeit
def load_sdn_ipams(
    neo4j_session: neo4j.Session,
    ipams: List[Dict[str, Any]],
    cluster_id: str,
    proxmox_update_tag: int,
) -> None:
    """
    Load SDN IPAMs into Neo4j.

    :param neo4j_session: Neo4j session
    :param ipams: Transformed IPAM data
    :param cluster_id: Cluster identifier
    :param proxmox_update_tag: Update tag for cleanup
    """
    load(
        neo4j_session,
        ProxmoxSDNIPAMSchema(),
        ipams,
        lastupdated=proxmox_update_tag,
        CLUSTER_ID=cluster_id,
    )


@timeit
def sync_sdn(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    proxmox_update_tag: int,
) -> None:
    """
    Sync all SDN resources for a Proxmox cluster.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmoxer API client
    :param cluster_id: Cluster identifier
    :param proxmox_update_tag: Update tag for cleanup
    """
    logger.info(f"Syncing SDN resources for cluster {cluster_id}")

    # Sync SDN zones
    zones_data = get_sdn_zones(proxmox_client)
    zones = transform_sdn_zones(zones_data, cluster_id)
    load_sdn_zones(neo4j_session, zones, cluster_id, proxmox_update_tag)

    # Sync SDN VNets
    vnets_data = get_sdn_vnets(proxmox_client)
    vnets = transform_sdn_vnets(vnets_data, cluster_id)
    load_sdn_vnets(neo4j_session, vnets, cluster_id, proxmox_update_tag)

    # Sync SDN subnets (for each VNet)
    all_subnets = []
    for vnet_data in vnets_data:
        vnet_id = vnet_data.get("vnet")
        if vnet_id:
            subnets_data = get_sdn_subnets(proxmox_client, vnet_id)
            subnets = transform_sdn_subnets(subnets_data, vnet_id, cluster_id)
            all_subnets.extend(subnets)
    load_sdn_subnets(neo4j_session, all_subnets, cluster_id, proxmox_update_tag)

    # Sync SDN controllers
    controllers_data = get_sdn_controllers(proxmox_client)
    controllers = transform_sdn_controllers(controllers_data, cluster_id)
    load_sdn_controllers(neo4j_session, controllers, cluster_id, proxmox_update_tag)

    # Sync SDN IPAMs
    ipams_data = get_sdn_ipams(proxmox_client)
    ipams = transform_sdn_ipams(ipams_data, cluster_id)
    load_sdn_ipams(neo4j_session, ipams, cluster_id, proxmox_update_tag)

    logger.info(
        f"Synced {len(zones)} zones, {len(vnets)} VNets, {len(all_subnets)} subnets, "
        f"{len(controllers)} controllers, {len(ipams)} IPAMs"
    )
