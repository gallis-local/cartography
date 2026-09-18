"""
Typed analysis jobs for the UniFi module.

Every job is scoped to the ``UnifiSite`` currently being synced. Scoping matters for
more than performance here: a UniFi deployment is commonly several controllers (or
several sites on one controller) ingested into one graph, and the unscoped predecessors
of these jobs joined nodes across site boundaries -- for example matching a port forward
in one site against a device that merely happened to reuse the same private IP in
another. The generated property cleanup is scoped the same way, so one site's analysis
run no longer wipes and recomputes every other site's flags.
"""

from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Case
from cartography.graph.analysis import RawCypher
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import Var

# Every UniFi node type hangs off its site by (:UnifiSite)-[:RESOURCE]->(:Unifi*), so one
# scope definition per anchored variable is all these jobs need.
_SITE_SCOPE_LABEL = "UnifiSite"
_SITE_SCOPE_PARAM = "site_id"


def _site_scope(*scope_on: str) -> ScopeById:
    """
    Build the per-site scope for an analysis job.

    :param scope_on: The anchored variable for each statement, in declaration order.
    :return: A ScopeById restricting the job and its generated cleanup to one site.
    """
    return ScopeById(
        _SITE_SCOPE_LABEL,
        _SITE_SCOPE_PARAM,
        scope_on=scope_on if len(scope_on) > 1 else scope_on[0],
    )


# Scoring buckets shared by the health/audit jobs: one issue is a warning, four or more
# is effectively unusable. Kept as a helper so the tiers cannot drift apart.
def _issue_count_score(issues_property: str, node: str) -> Case:
    """
    Score a node from 100 down to 20 by how many issues were recorded against it.

    :param issues_property: Name of the list property holding the issue strings.
    :param node: Cypher variable for the node being scored.
    :return: A Case expression yielding the score.
    """
    size_expr = f"size(coalesce({node}.{issues_property}, []))"
    return Case(
        when=(
            (f"{size_expr} = 0", 100),
            (f"{size_expr} = 1", 80),
            (f"{size_expr} = 2", 60),
            (f"{size_expr} = 3", 40),
        ),
        else_=20,
    )


UNIFI_INTERNET_EXPOSURE = AnalysisJob(
    name="UniFi asset internet exposure",
    short_name="unifi_internet_exposure",
    scope=_site_scope("d", "d", "pf", "w", "w", "d"),
    statements=(
        AnalysisStatement(
            comment="A device that holds a WAN address is reachable from the internet by definition.",
            match="MATCH (d:UnifiDevice) WHERE d.last_wan_ip IS NOT NULL",
            effects=(
                SetProperty("d", "exposed_internet", True, label="UnifiDevice"),
                AddToSet("d", "exposed_internet_type", "wan_ip", label="UnifiDevice"),
            ),
        ),
        AnalysisStatement(
            # The port forward is matched through `scope` rather than globally: forward_ip
            # values are private addresses, so an unscoped join flagged same-IP devices in
            # unrelated sites.
            comment="A device that an enabled port forward in the same site points at is published to the internet.",
            match=(
                "MATCH (d:UnifiDevice) "
                "MATCH (scope)-[:RESOURCE]->(pf:UnifiPortForward) "
                "WHERE pf.enabled = true AND pf.forward_ip IS NOT NULL AND d.ip = pf.forward_ip "
                "WITH DISTINCT d"
            ),
            effects=(
                SetProperty("d", "exposed_internet", True, label="UnifiDevice"),
                AddToSet(
                    "d", "exposed_internet_type", "port_forward", label="UnifiDevice"
                ),
            ),
        ),
        AnalysisStatement(
            comment="The port forward rule itself is an internet-facing entry point.",
            match="MATCH (pf:UnifiPortForward) WHERE pf.enabled = true AND pf.forward_ip IS NOT NULL",
            effects=(
                SetProperty("pf", "exposed_internet", True, label="UnifiPortForward"),
                AddToSet(
                    "pf",
                    "exposed_internet_type",
                    "port_forward",
                    label="UnifiPortForward",
                ),
            ),
        ),
        AnalysisStatement(
            comment="An enabled WLAN with no link-layer encryption is joinable by anyone in radio range.",
            match="MATCH (w:UnifiWlan) WHERE w.enabled = true AND (w.security = 'open' OR w.security IS NULL)",
            effects=(
                SetProperty("w", "exposed_internet", True, label="UnifiWlan"),
                AddToSet("w", "exposed_internet_type", "open_wlan", label="UnifiWlan"),
            ),
        ),
        AnalysisStatement(
            comment="A guest WLAN is intended to carry untrusted devices straight to the internet.",
            match="MATCH (w:UnifiWlan) WHERE w.enabled = true AND w.is_guest = true",
            effects=(
                SetProperty("w", "exposed_internet", True, label="UnifiWlan"),
                AddToSet("w", "exposed_internet_type", "guest_wlan", label="UnifiWlan"),
            ),
        ),
        AnalysisStatement(
            # Depends on the two WLAN statements above having already run.
            comment="An access point inherits the exposure of the WLANs it broadcasts.",
            match="MATCH (d:UnifiDevice)-[:BROADCASTS]->(w:UnifiWlan) WHERE w.exposed_internet = true",
            effects=(
                SetProperty("d", "exposed_internet", True, label="UnifiDevice"),
                AddToSet(
                    "d",
                    "exposed_internet_type",
                    "broadcasts_exposed_wlan",
                    label="UnifiDevice",
                ),
            ),
        ),
    ),
)

UNIFI_FIRMWARE_COMPLIANCE = AnalysisJob(
    name="UniFi firmware compliance",
    short_name="unifi_firmware_compliance",
    scope=_site_scope("d"),
    statements=(
        AnalysisStatement(
            comment="The controller offers a newer firmware than the device is running.",
            match=(
                "MATCH (d:UnifiDevice) "
                "WHERE d.upgradable = true AND d.version IS NOT NULL "
                "AND d.upgrade_to_firmware IS NOT NULL AND d.version <> d.upgrade_to_firmware"
            ),
            effects=(
                SetProperties(
                    "d",
                    {
                        "firmware_compliant": False,
                        "firmware_version_current": Var("d.version"),
                        "firmware_version_latest": Var("d.upgrade_to_firmware"),
                    },
                    label="UnifiDevice",
                ),
            ),
        ),
        AnalysisStatement(
            # Only devices the controller positively reports as up to date are marked
            # compliant. A device with an unknown upgrade state is left unflagged rather
            # than defaulted to true, so "compliant" never means "we could not tell".
            comment="The controller reports no pending firmware upgrade for the device.",
            match=(
                "MATCH (d:UnifiDevice) "
                "WHERE d.upgradable = false "
                "OR (d.version IS NOT NULL AND d.version = d.upgrade_to_firmware)"
            ),
            effects=(
                SetProperties(
                    "d",
                    {
                        "firmware_compliant": True,
                        "firmware_version_current": Var("d.version"),
                        "firmware_version_latest": Var("d.upgrade_to_firmware"),
                    },
                    label="UnifiDevice",
                ),
            ),
        ),
    ),
)

UNIFI_GUEST_ISOLATION = AnalysisJob(
    name="UniFi guest network isolation",
    short_name="unifi_guest_isolation",
    scope=_site_scope("w", "w", "w", "v", "c", "c"),
    statements=(
        AnalysisStatement(
            comment="Mark the WLANs the controller designates as guest networks.",
            match="MATCH (w:UnifiWlan) WHERE w.is_guest = true",
            effects=(SetProperty("w", "guest_isolated", True, label="UnifiWlan"),),
        ),
        AnalysisStatement(
            comment="An unencrypted guest WLAN exposes guest traffic to passive capture.",
            match="MATCH (w:UnifiWlan) WHERE w.is_guest = true AND (w.security = 'open' OR w.security IS NULL)",
            effects=(
                AddToSet(
                    "w", "guest_isolation_issues", "open_security", label="UnifiWlan"
                ),
            ),
        ),
        AnalysisStatement(
            comment="A guest WLAN without MAC filtering cannot restrict which devices associate.",
            match="MATCH (w:UnifiWlan) WHERE w.is_guest = true AND w.mac_filter_enabled = false",
            effects=(
                AddToSet(
                    "w", "guest_isolation_issues", "no_mac_filter", label="UnifiWlan"
                ),
            ),
        ),
        AnalysisStatement(
            # Collected as a list: a site can run more than one guest WLAN, and the
            # previous single-valued form silently kept whichever row Neo4j returned last.
            comment="Record every guest WLAN a hotspot voucher can be redeemed against.",
            match=(
                "MATCH (v:UnifiVoucher) WHERE v.for_hotspot = true "
                "AND v.status IN ['VALID_MULTI', 'USED_MULTIPLE'] "
                "MATCH (scope)-[:RESOURCE]->(w:UnifiWlan) WHERE w.is_guest = true"
            ),
            effects=(
                AddToSet("v", "guest_networks", Var("w.name"), label="UnifiVoucher"),
            ),
        ),
        AnalysisStatement(
            # Traverses CONNECTED_TO_WLAN instead of comparing a `wlanconf_id` property:
            # the client model never declared that property, so the property comparison
            # matched nothing and no client was ever marked isolated.
            comment="A guest client sitting on a guest WLAN is correctly isolated.",
            match=(
                "MATCH (c:UnifiClient)-[:CONNECTED_TO_WLAN]->(w:UnifiWlan) "
                "WHERE c.is_guest = true AND w.is_guest = true"
            ),
            effects=(SetProperty("c", "guest_isolated", True, label="UnifiClient"),),
        ),
        AnalysisStatement(
            comment="A guest client on a non-guest WLAN has escaped the guest segment.",
            match=(
                "MATCH (c:UnifiClient)-[:CONNECTED_TO_WLAN]->(w:UnifiWlan) "
                "WHERE c.is_guest = true AND w.is_guest = false"
            ),
            effects=(
                AddToSet(
                    "c",
                    "guest_isolation_issues",
                    "guest_on_non_guest_wlan",
                    label="UnifiClient",
                ),
            ),
        ),
    ),
)

UNIFI_DEVICE_HEALTH = AnalysisJob(
    name="UniFi device health assessment",
    short_name="unifi_device_health",
    scope=_site_scope("d", "d", "d", "d", "d", "d"),
    statements=(
        AnalysisStatement(
            comment="The device reports itself as running hot.",
            match="MATCH (d:UnifiDevice) WHERE d.overheating = true",
            effects=(
                SetProperty(
                    "d", "temperature_status", "overheating", label="UnifiDevice"
                ),
                AddToSet("d", "health_issues", "overheating", label="UnifiDevice"),
            ),
        ),
        AnalysisStatement(
            # toFloat() because the controller reports these AC figures as decimal strings.
            comment="The device is drawing within 10% of its AC power budget.",
            match=(
                "MATCH (d:UnifiDevice) "
                "WHERE d.outlet_ac_power_consumption IS NOT NULL "
                "AND d.outlet_ac_power_budget IS NOT NULL "
                "AND toFloat(d.outlet_ac_power_consumption) > toFloat(d.outlet_ac_power_budget) * 0.9"
            ),
            effects=(
                SetProperty("d", "power_status", "near_capacity", label="UnifiDevice"),
                AddToSet(
                    "d", "health_issues", "power_near_capacity", label="UnifiDevice"
                ),
            ),
        ),
        AnalysisStatement(
            comment="The device has a pending firmware upgrade.",
            match="MATCH (d:UnifiDevice) WHERE d.upgradable = true",
            effects=(
                AddToSet(
                    "d", "health_issues", "firmware_outdated", label="UnifiDevice"
                ),
            ),
        ),
        AnalysisStatement(
            comment="The controller has lost contact with the device.",
            match="MATCH (d:UnifiDevice) WHERE d.state IN ['DISCONNECTED', 'ISOLATED']",
            effects=(
                AddToSet("d", "health_issues", "disconnected", label="UnifiDevice"),
            ),
        ),
        AnalysisStatement(
            comment="Deeply nested uplinks add latency and widen the blast radius of one failure.",
            match="MATCH (d:UnifiDevice) WHERE d.uplink_depth IS NOT NULL AND d.uplink_depth > 3",
            effects=(
                AddToSet(
                    "d", "health_issues", "deep_uplink_topology", label="UnifiDevice"
                ),
            ),
        ),
        AnalysisStatement(
            comment="Roll the recorded issues up into a single comparable score.",
            match="MATCH (d:UnifiDevice)",
            effects=(
                SetProperty(
                    "d",
                    "health_score",
                    _issue_count_score("health_issues", "d"),
                    label="UnifiDevice",
                ),
            ),
        ),
    ),
)

UNIFI_NETWORK_CONFIG_AUDIT = AnalysisJob(
    name="UniFi network configuration audit",
    short_name="unifi_network_config_audit",
    scope=_site_scope("c", "c", "c", "c", "c", "c", "c"),
    statements=(
        AnalysisStatement(
            comment="A disabled network definition is dead configuration that still carries a subnet.",
            match="MATCH (c:UnifiNetworkConfig) WHERE c.enabled = false",
            effects=(
                AddToSet(
                    "c", "audit_issues", "disabled_config", label="UnifiNetworkConfig"
                ),
            ),
        ),
        AnalysisStatement(
            comment="VLAN tagging is switched on but no VLAN ID was assigned, so the tag is undefined.",
            match="MATCH (c:UnifiNetworkConfig) WHERE c.vlan_enabled = true AND c.vlan IS NULL",
            effects=(
                AddToSet(
                    "c",
                    "audit_issues",
                    "vlan_enabled_without_vlan_id",
                    label="UnifiNetworkConfig",
                ),
            ),
        ),
        AnalysisStatement(
            comment="A guest network without DHCP cannot address the untrusted clients it is for.",
            match="MATCH (c:UnifiNetworkConfig) WHERE c.is_guest = true AND c.dhcpd_enabled = false",
            effects=(
                AddToSet(
                    "c",
                    "audit_issues",
                    "guest_network_without_dhcp",
                    label="UnifiNetworkConfig",
                ),
            ),
        ),
        AnalysisStatement(
            comment="A guest network that is not NATted routes untranslated guest traffic inward.",
            match="MATCH (c:UnifiNetworkConfig) WHERE c.is_guest = true AND c.is_nat = false",
            effects=(
                AddToSet(
                    "c",
                    "audit_issues",
                    "guest_network_not_natted",
                    label="UnifiNetworkConfig",
                ),
            ),
        ),
        AnalysisStatement(
            comment="DHCP is told to advertise DNS but no DNS server was configured.",
            match=(
                "MATCH (c:UnifiNetworkConfig) "
                "WHERE c.dhcpd_enabled = true AND c.dhcpd_dns_enabled = true AND c.dhcpd_dns_1 IS NULL"
            ),
            effects=(
                AddToSet(
                    "c",
                    "audit_issues",
                    "dhcp_dns_enabled_without_dns_server",
                    label="UnifiNetworkConfig",
                ),
            ),
        ),
        AnalysisStatement(
            comment="Roll the recorded issues up into a single comparable score.",
            match="MATCH (c:UnifiNetworkConfig)",
            effects=(
                SetProperty(
                    "c",
                    "audit_score",
                    _issue_count_score("audit_issues", "c"),
                    label="UnifiNetworkConfig",
                ),
            ),
        ),
        AnalysisStatement(
            comment="Bucket the score into a tier for reporting.",
            match="MATCH (c:UnifiNetworkConfig)",
            effects=(
                SetProperty(
                    "c",
                    "audit_tier",
                    Case(
                        when=(
                            ("c.audit_score >= 90", "compliant"),
                            ("c.audit_score >= 70", "minor_issues"),
                            ("c.audit_score >= 40", "major_issues"),
                        ),
                        else_="non_compliant",
                    ),
                    label="UnifiNetworkConfig",
                ),
            ),
        ),
    ),
)

UNIFI_POWER_MONITORING = AnalysisJob(
    name="UniFi power monitoring",
    short_name="unifi_power_monitoring",
    scope=_site_scope("o", "o", "o", "o", "o"),
    statements=(
        AnalysisStatement(
            comment="The outlet is drawing more than a kilowatt.",
            match="MATCH (o:UnifiOutlet) WHERE o.has_metering = true AND o.power IS NOT NULL AND toFloat(o.power) > 1000",
            effects=(
                AddToSet("o", "power_issues", "high_power_draw", label="UnifiOutlet"),
            ),
        ),
        AnalysisStatement(
            comment="A switchable outlet is currently off, so whatever is plugged into it is unpowered.",
            match="MATCH (o:UnifiOutlet) WHERE o.has_relay = true AND o.relay_state = false",
            effects=(AddToSet("o", "power_issues", "outlet_off", label="UnifiOutlet"),),
        ),
        AnalysisStatement(
            comment="The outlet supports metering but it is switched off, leaving no power telemetry.",
            match="MATCH (o:UnifiOutlet) WHERE o.caps IS NOT NULL AND o.caps >= 3 AND o.has_metering = false",
            effects=(
                AddToSet(
                    "o",
                    "power_issues",
                    "metering_capable_but_disabled",
                    label="UnifiOutlet",
                ),
            ),
        ),
        AnalysisStatement(
            # The power > 0 guard is load-bearing: an idle outlet reports a power factor of
            # 0, so without it every unused-but-metered outlet was reported as having a
            # poor power factor. Power factor is only meaningful under load.
            comment="The outlet is under load but converting power inefficiently.",
            match=(
                "MATCH (o:UnifiOutlet) "
                "WHERE o.has_metering = true AND o.power IS NOT NULL AND toFloat(o.power) > 0 "
                "AND o.power_factor IS NOT NULL AND toFloat(o.power_factor) < 0.8"
            ),
            effects=(
                AddToSet("o", "power_issues", "poor_power_factor", label="UnifiOutlet"),
            ),
        ),
        AnalysisStatement(
            comment="Summarise the recorded issues into a single status.",
            match="MATCH (o:UnifiOutlet)",
            effects=(
                SetProperty(
                    "o",
                    "power_status",
                    Case(
                        when=(
                            ("size(coalesce(o.power_issues, [])) = 0", "healthy"),
                            ("size(coalesce(o.power_issues, [])) = 1", "warning"),
                        ),
                        else_="critical",
                    ),
                    label="UnifiOutlet",
                ),
            ),
        ),
    ),
)

UNIFI_WAN_PERFORMANCE = AnalysisJob(
    name="UniFi WAN performance analysis",
    short_name="unifi_wan_performance",
    scope=_site_scope("s", "s", "s", "s", "s", "s", "s"),
    statements=(
        AnalysisStatement(
            # Without this branch a speedtest that never returned figures scored 100
            # "excellent", because every threshold comparison against NULL is NULL and the
            # empty-issues default then took over. Missing telemetry is not good telemetry.
            comment="The speedtest is missing one of its three metrics, so it cannot be judged.",
            match=(
                "MATCH (s:UnifiSpeedtest) "
                "WHERE s.download IS NULL OR s.upload IS NULL OR s.ping IS NULL"
            ),
            effects=(
                AddToSet(
                    "s", "performance_issues", "missing_metrics", label="UnifiSpeedtest"
                ),
            ),
        ),
        AnalysisStatement(
            comment="Download throughput is below a usable broadband floor.",
            match="MATCH (s:UnifiSpeedtest) WHERE s.download < 25",
            effects=(
                AddToSet(
                    "s", "performance_issues", "low_download", label="UnifiSpeedtest"
                ),
            ),
        ),
        AnalysisStatement(
            comment="Upload throughput is below a usable broadband floor.",
            match="MATCH (s:UnifiSpeedtest) WHERE s.upload < 5",
            effects=(
                AddToSet(
                    "s", "performance_issues", "low_upload", label="UnifiSpeedtest"
                ),
            ),
        ),
        AnalysisStatement(
            comment="Round-trip latency is high enough to degrade interactive traffic.",
            match="MATCH (s:UnifiSpeedtest) WHERE s.ping > 100",
            effects=(
                AddToSet(
                    "s", "performance_issues", "high_latency", label="UnifiSpeedtest"
                ),
            ),
        ),
        AnalysisStatement(
            # Materialised as an empty list rather than left absent so that consumers can
            # distinguish "assessed, no issues" from "not assessed".
            comment="Give issue-free speedtests an explicit empty issue list.",
            match="MATCH (s:UnifiSpeedtest) WHERE s.performance_issues IS NULL",
            effects=(
                SetProperty(
                    "s", "performance_issues", RawCypher("[]"), label="UnifiSpeedtest"
                ),
            ),
        ),
        AnalysisStatement(
            # Left NULL (i.e. absent) when metrics are missing: any numeric score would be
            # a fabricated grade for a measurement that never happened.
            comment="Score the speedtest by how many thresholds it missed.",
            match="MATCH (s:UnifiSpeedtest)",
            effects=(
                SetProperty(
                    "s",
                    "performance_score",
                    Case(
                        when=(
                            (
                                "'missing_metrics' IN coalesce(s.performance_issues, [])",
                                None,
                            ),
                            ("size(coalesce(s.performance_issues, [])) = 0", 100),
                            ("size(coalesce(s.performance_issues, [])) = 1", 70),
                            ("size(coalesce(s.performance_issues, [])) = 2", 40),
                        ),
                        else_=20,
                    ),
                    label="UnifiSpeedtest",
                ),
            ),
        ),
        AnalysisStatement(
            comment="Bucket the score into a tier for reporting.",
            match="MATCH (s:UnifiSpeedtest)",
            effects=(
                SetProperty(
                    "s",
                    "performance_tier",
                    Case(
                        when=(
                            ("s.performance_score IS NULL", "unknown"),
                            ("s.performance_score >= 90", "excellent"),
                            ("s.performance_score >= 70", "good"),
                            ("s.performance_score >= 40", "fair"),
                        ),
                        else_="poor",
                    ),
                    label="UnifiSpeedtest",
                ),
            ),
        ),
    ),
)

# Declaration order is execution order. UNIFI_INTERNET_EXPOSURE must run before nothing
# else here, but UNIFI_GUEST_ISOLATION reads no analysis output, so the ordering is only
# for readability.
UNIFI_ANALYSIS_JOBS = (
    UNIFI_INTERNET_EXPOSURE,
    UNIFI_FIRMWARE_COMPLIANCE,
    UNIFI_GUEST_ISOLATION,
    UNIFI_DEVICE_HEALTH,
    UNIFI_NETWORK_CONFIG_AUDIT,
    UNIFI_POWER_MONITORING,
    UNIFI_WAN_PERFORMANCE,
)
