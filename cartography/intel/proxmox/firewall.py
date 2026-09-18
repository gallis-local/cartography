"""
Sync Proxmox firewall configurations.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.proxmox.util import log_optional_fetch_failure
from cartography.models.proxmox.firewall import ProxmoxFirewallIPSetSchema
from cartography.models.proxmox.firewall import ProxmoxFirewallRuleSchema
from cartography.models.proxmox.firewall import ProxmoxFirewallRuleToIPSetMatchLink
from cartography.models.proxmox.firewall import ProxmoxFirewallRuleToNodeMatchLink
from cartography.models.proxmox.firewall import ProxmoxFirewallRuleToVMMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cluster_firewall_rules(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get cluster-level firewall rules.

    :param proxmox_client: Proxmox API client
    :return: List of firewall rule dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.firewall.rules.get()


@timeit
def get_node_firewall_rules(
    proxmox_client: Any, node_name: str
) -> list[dict[str, Any]]:
    """
    Get node-level firewall rules.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of firewall rule dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes(node_name).firewall.rules.get()


@timeit
def get_vm_firewall_rules(
    proxmox_client: Any, node_name: str, vmid: int, vm_type: str
) -> list[dict[str, Any]]:
    """
    Get VM- or container-level firewall rules.

    Returns an empty list rather than raising if the guest's firewall endpoint is
    unavailable, so one unreadable guest does not lose the rules of every other one.

    :param proxmox_client: Proxmox API client
    :param node_name: Name of the node hosting the guest
    :param vmid: Guest VMID
    :param vm_type: Either "qemu" or "lxc"
    :return: List of firewall rule dicts
    """
    from proxmoxer.core import ResourceException
    from requests.exceptions import RequestException

    # Deliberate departure from the "let get() fail loudly" convention: this is
    # fetched once per guest, so one refusal must not cost us the other
    # guests. Collection-level fetches in this module do let errors propagate to
    # the orchestrator's best-effort wrapper.
    try:
        node = proxmox_client.nodes(node_name)
        if vm_type == "qemu":
            return node.qemu(vmid).firewall.rules.get()
        if vm_type == "lxc":
            return node.lxc(vmid).firewall.rules.get()
        logger.warning("Unknown VM type %s for vmid %s", vm_type, vmid)
        return []
    except (ResourceException, RequestException) as e:
        log_optional_fetch_failure(e, "guest firewall rules", vmid=vmid, node=node_name)
        return []


@timeit
def get_cluster_ipsets(proxmox_client: Any) -> list[dict[str, Any]]:
    """
    Get cluster-level IP sets.

    :param proxmox_client: Proxmox API client
    :return: List of IP set dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.firewall.ipset.get()


@timeit
def get_ipset_cidrs(proxmox_client: Any, ipset_name: str) -> list[dict[str, Any]]:
    """
    Get CIDR entries for a specific IP set.

    :param proxmox_client: Proxmox API client
    :param ipset_name: IP set name
    :return: List of CIDR entry dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.firewall.ipset(ipset_name).get()


def _extract_ipset_references(value: str | None) -> list[str]:
    """
    Extract IPSet names from source/dest fields.

    Proxmox firewall rules reference IPSets with a + prefix (e.g., +my_ipset).

    :param value: Source or dest field value
    :return: List of IPSet names (without + prefix)
    """
    if not value:
        return []

    ipsets = []
    # Value can be comma-separated list of addresses/ipsets
    for part in value.split(","):
        part = part.strip()
        if part.startswith("+"):
            ipsets.append(part[1:])  # Remove + prefix
    return ipsets


def transform_firewall_rule_data(
    rules: list[dict[str, Any]],
    cluster_id: str,
    scope: str,
    scope_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Transform firewall rule data into standard format.

    :param rules: Raw firewall rule data from API
    :param cluster_id: Parent cluster ID
    :param scope: Rule scope (cluster, node, vm)
    :param scope_id: Scope identifier (node name or vmid)
    :return: List of transformed firewall rule dicts
    """
    transformed_rules = []

    for rule in rules:
        pos = rule.get("pos", 0)
        if scope == "cluster":
            rule_id = f"{cluster_id}/firewall/rule/{pos}"
        elif scope == "node":
            rule_id = f"{cluster_id}/node/{scope_id}/firewall/rule/{pos}"
        elif scope == "vm":
            rule_id = f"{cluster_id}/vm/{scope_id}/firewall/rule/{pos}"
        else:
            # Fallback for unknown scopes
            rule_id = (
                f"{cluster_id}/firewall/{scope}/{scope_id}/rule/{pos}"
                if scope_id
                else f"{cluster_id}/firewall/{scope}/rule/{pos}"
            )

        # Build full scope ID for relationship matching
        # For node-scoped rules, need full node ID for matching
        full_scope_id = scope_id
        if scope == "node" and scope_id:
            full_scope_id = f"{cluster_id}/node/{scope_id}"
        elif scope == "vm" and scope_id:
            full_scope_id = f"{cluster_id}/vm/{scope_id}"

        # Extract IPSet references from source/dest
        source = rule.get("source")
        dest = rule.get("dest")
        source_ipsets = _extract_ipset_references(source)
        dest_ipsets = _extract_ipset_references(dest)

        transformed_rules.append(
            {
                "id": rule_id,
                "cluster_id": cluster_id,
                "scope": scope,
                "scope_id": full_scope_id,  # Use full ID for relationship matching
                "pos": rule.get("pos", 0),
                "type": rule.get("type"),
                "action": rule.get("action"),
                "enable": bool(rule.get("enable", True)),  # Convert to bool
                "iface": rule.get("iface"),
                "source": source,
                "dest": dest,
                "proto": rule.get("proto"),
                "sport": rule.get("sport"),
                "dport": rule.get("dport"),
                "comment": rule.get("comment"),
                "macro": rule.get("macro"),
                "log": rule.get("log"),
                # IPSet references for relationship creation
                "source_ipsets": source_ipsets if source_ipsets else None,
                "dest_ipsets": dest_ipsets if dest_ipsets else None,
            }
        )

    return transformed_rules


def transform_ipset_data(
    ipsets: list[dict[str, Any]],
    ipset_cidrs: dict[str, list[dict[str, Any]]],
    cluster_id: str,
    scope: str,
    scope_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Transform IP set data into standard format.

    :param ipsets: Raw IP set data from API
    :param ipset_cidrs: Map of ipset name -> CIDR entries
    :param cluster_id: Parent cluster ID
    :param scope: IP set scope (cluster, node, vm)
    :param scope_id: Scope identifier
    :return: List of transformed IP set dicts
    """
    transformed_ipsets = []

    for ipset in ipsets:
        name = ipset["name"]
        if scope == "cluster":
            ipset_id = f"{cluster_id}/firewall/ipset/{name}"
        elif scope == "node":
            ipset_id = f"{cluster_id}/node/{scope_id}/firewall/ipset/{name}"
        elif scope == "vm":
            ipset_id = f"{cluster_id}/vm/{scope_id}/firewall/ipset/{name}"
        else:
            # Fallback for unknown scopes
            ipset_id = (
                f"{cluster_id}/firewall/{scope}/{scope_id}/ipset/{name}"
                if scope_id
                else f"{cluster_id}/firewall/{scope}/ipset/{name}"
            )

        # Get CIDR entries for this IP set
        cidrs = []
        for cidr_entry in ipset_cidrs.get(name, []):
            if "cidr" in cidr_entry:
                cidrs.append(cidr_entry["cidr"])

        transformed_ipsets.append(
            {
                "id": ipset_id,
                "name": name,
                "cluster_id": cluster_id,
                "scope": scope,
                "scope_id": scope_id,
                "comment": ipset.get("comment"),
                "cidrs": cidrs,
            }
        )

    return transformed_ipsets


def load_firewall_rules(
    neo4j_session: neo4j.Session,
    rules: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load firewall rule data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param rules: List of transformed firewall rule dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not rules:
        return

    load(
        neo4j_session,
        ProxmoxFirewallRuleSchema(),
        rules,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_ipsets(
    neo4j_session: neo4j.Session,
    ipsets: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load IP set data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param ipsets: List of transformed IP set dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not ipsets:
        return

    load(
        neo4j_session,
        ProxmoxFirewallIPSetSchema(),
        ipsets,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_firewall_scope_relationships(
    neo4j_session: neo4j.Session,
    rules: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Create relationships between firewall rules and their scope (node or VM).

    Uses MatchLinks to connect firewall rules to nodes and VMs.

    :param neo4j_session: Neo4j session
    :param rules: List of firewall rule dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    # Separate rules by scope
    node_rules = [r for r in rules if r["scope"] == "node" and r["scope_id"]]
    vm_rules = [r for r in rules if r["scope"] == "vm" and r["scope_id"]]

    # Create relationships to nodes
    if node_rules:
        load_matchlinks(
            neo4j_session,
            ProxmoxFirewallRuleToNodeMatchLink(),
            node_rules,
            lastupdated=update_tag,
            _sub_resource_label="ProxmoxCluster",
            _sub_resource_id=cluster_id,
        )

    # Create relationships to VMs
    if vm_rules:
        # scope_id for VM rules is the full VM path (e.g. "cluster1/vm/100").
        # Extract the integer VMID from the trailing segment.
        for rule in vm_rules:
            if rule["scope_id"]:
                try:
                    rule["vmid_int"] = int(rule["scope_id"].split("/")[-1])
                except (ValueError, IndexError):
                    pass

        load_matchlinks(
            neo4j_session,
            ProxmoxFirewallRuleToVMMatchLink(),
            vm_rules,
            lastupdated=update_tag,
            _sub_resource_label="ProxmoxCluster",
            _sub_resource_id=cluster_id,
        )


def load_firewall_ipset_relationships(
    neo4j_session: neo4j.Session,
    rules: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Create USES_IPSET relationships between firewall rules and referenced IPSets.

    This enables security analysis like:
    - Finding overly permissive rules using IPSets with 0.0.0.0/0
    - Tracking which rules depend on specific IP ranges
    - Impact analysis when modifying an IPSet

    Uses MatchLinks to connect firewall rules to IPSets.

    :param neo4j_session: Neo4j session
    :param rules: List of firewall rule dicts with source_ipsets/dest_ipsets
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    # Find rules that reference IPSets and expand to individual relationships
    ipset_relationships = []
    for rule in rules:
        source_ipsets = rule.get("source_ipsets") or []
        dest_ipsets = rule.get("dest_ipsets") or []
        all_ipsets = set(source_ipsets + dest_ipsets)  # Deduplicate

        for ipset_name in all_ipsets:
            ipset_relationships.append(
                {
                    "id": rule["id"],
                    "cluster_id": rule["cluster_id"],
                    "ipset_name": ipset_name,
                    "in_source": ipset_name in source_ipsets,
                    "in_dest": ipset_name in dest_ipsets,
                }
            )

    if not ipset_relationships:
        return

    load_matchlinks(
        neo4j_session,
        ProxmoxFirewallRuleToIPSetMatchLink(),
        ipset_relationships,
        lastupdated=update_tag,
        _sub_resource_label="ProxmoxCluster",
        _sub_resource_id=cluster_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    enable_vm_firewall_rules: bool = False,
) -> None:
    """
    Sync firewall configuration.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    :param enable_vm_firewall_rules: Also sync per-guest firewall rules. Off by
        default because it costs one extra API call per VM and container.
    """
    logger.info("Syncing Proxmox firewall configuration")

    all_rules = []
    all_ipsets = []

    cluster_rules = get_cluster_firewall_rules(proxmox_client)
    transformed_cluster_rules = transform_firewall_rule_data(
        cluster_rules, cluster_id, "cluster"
    )
    all_rules.extend(transformed_cluster_rules)

    cluster_ipsets = get_cluster_ipsets(proxmox_client)
    ipset_cidrs = {}
    for ipset in cluster_ipsets:
        ipset_name = ipset["name"]
        cidrs = get_ipset_cidrs(proxmox_client, ipset_name)
        ipset_cidrs[ipset_name] = cidrs

    transformed_ipsets = transform_ipset_data(
        cluster_ipsets, ipset_cidrs, cluster_id, "cluster"
    )
    all_ipsets.extend(transformed_ipsets)

    # VM-level rules cost one API call per guest, so they are opt-in. Say so when
    # they are off: no vm-scoped ProxmoxFirewallRule nodes would otherwise read as
    # "no guest firewall rules exist" rather than "we never asked".
    if not enable_vm_firewall_rules:
        logger.info(
            "Skipping VM-level Proxmox firewall rules; enable with "
            "--proxmox-enable-vm-firewall-rules. This costs one API call per guest."
        )

    nodes = proxmox_client.nodes.get()
    guest_count = 0
    for node in nodes:
        node_name = node["node"]
        node_rules = get_node_firewall_rules(proxmox_client, node_name)
        transformed_node_rules = transform_firewall_rule_data(
            node_rules, cluster_id, "node", node_name
        )
        all_rules.extend(transformed_node_rules)

        if not enable_vm_firewall_rules:
            continue

        for vm_type in ("qemu", "lxc"):
            for guest in getattr(proxmox_client.nodes(node_name), vm_type).get():
                vmid = guest["vmid"]
                guest_count += 1
                vm_rules = get_vm_firewall_rules(
                    proxmox_client, node_name, vmid, vm_type
                )
                all_rules.extend(
                    transform_firewall_rule_data(vm_rules, cluster_id, "vm", str(vmid))
                )

    if enable_vm_firewall_rules:
        logger.info("Fetched VM-level firewall rules for %d guests", guest_count)

    load_firewall_rules(neo4j_session, all_rules, cluster_id, update_tag)
    load_ipsets(neo4j_session, all_ipsets, cluster_id, update_tag)

    if all_rules:
        load_firewall_scope_relationships(
            neo4j_session, all_rules, cluster_id, update_tag
        )
        # Create relationships between rules and IPSets they reference
        load_firewall_ipset_relationships(
            neo4j_session, all_rules, cluster_id, update_tag
        )

    logger.debug(
        "Synced %d firewall rules and %d IP sets", len(all_rules), len(all_ipsets)
    )

    cleanup(neo4j_session, common_job_parameters, cluster_id, update_tag)


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Remove stale firewall data.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common parameters for GraphJob
    :param cluster_id: Cluster ID for MatchLink cleanup scoping
    :param update_tag: Sync timestamp for MatchLink cleanup
    """
    GraphJob.from_node_schema(ProxmoxFirewallRuleSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ProxmoxFirewallIPSetSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_matchlink(
        ProxmoxFirewallRuleToNodeMatchLink(), "ProxmoxCluster", cluster_id, update_tag
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        ProxmoxFirewallRuleToVMMatchLink(), "ProxmoxCluster", cluster_id, update_tag
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        ProxmoxFirewallRuleToIPSetMatchLink(), "ProxmoxCluster", cluster_id, update_tag
    ).run(neo4j_session)
