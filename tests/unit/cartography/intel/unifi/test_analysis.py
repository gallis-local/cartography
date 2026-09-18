"""
Unit tests for the typed UniFi analysis jobs.

These jobs are only observable through the Cypher they compile to, so the tests here
assert on the compiled queries. They exist mainly as regression guards for four defects
that were live in the JSON predecessors of these jobs and that all failed the same silent
way -- a statement matched nothing, so a security flag read "clean" for every node:

* a property compared against a name no node model declares (``UnifiClient.wlanconf_id``)
* a relationship traversed in the wrong direction (``(:UnifiWlan)-[:RESOURCE]->(:UnifiSite)``)
* a flag set on a label the cleanup statement never covered, so it never reset
* a statement joining nodes across site boundaries
"""

import dataclasses
import importlib
import pkgutil
import re

import pytest

import cartography.models.unifi
from cartography.analysis.unifi.analysis import UNIFI_ANALYSIS_JOBS
from cartography.analysis.unifi.analysis import UNIFI_GUEST_ISOLATION
from cartography.analysis.unifi.analysis import UNIFI_POWER_MONITORING
from cartography.analysis.unifi.analysis import UNIFI_WAN_PERFORMANCE
from cartography.graph.analysisbuilder import properties_set
from cartography.graph.analysisbuilder import to_graph_job
from cartography.intel.unifi.util import attach_scoped_ids
from cartography.intel.unifi.util import scoped_id
from cartography.intel.unifi.util import scoped_ids
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.unifi.client import UnifiClientSchema
from cartography.models.unifi.device import UnifiDeviceSchema

# Cypher functions and keywords that look like `alias.property` dereferences but are not.
_PROPERTY_REF = re.compile(r"\b([a-z][a-z0-9_]*)\.([a-z][a-z0-9_]*)\b")


def _declared_properties() -> dict[str, set[str]]:
    """
    Collect the properties each UniFi node schema actually declares.

    :return: Mapping of node label to the set of property names the model defines.
    """
    declared: dict[str, set[str]] = {}
    for module_info in pkgutil.iter_modules(cartography.models.unifi.__path__):
        module = importlib.import_module(f"cartography.models.unifi.{module_info.name}")
        for attribute in vars(module).values():
            if (
                isinstance(attribute, type)
                and issubclass(attribute, CartographyNodeSchema)
                and attribute is not CartographyNodeSchema
            ):
                schema = attribute()
                declared[schema.label] = {
                    field.name for field in dataclasses.fields(schema.properties)
                }
    return declared


def _alias_labels(match: str) -> dict[str, str]:
    """
    Map each Cypher variable in a match clause to the label it is bound to.

    :param match: The statement's match clause.
    :return: Mapping of variable name to node label.
    """
    return dict(re.findall(r"\(\s*([a-z][a-z0-9_]*)\s*:\s*(Unifi[A-Za-z]+)", match))


def _written_properties() -> dict[str, set[str]]:
    """
    Collect the properties the analysis jobs themselves add to each label.

    Later statements legitimately read the flags earlier statements wrote, so these count
    as valid references even though no node model declares them.

    :return: Mapping of node label to the set of analysis-written property names.
    """
    written: dict[str, set[str]] = {}
    for job in UNIFI_ANALYSIS_JOBS:
        for effect in properties_set(job):
            label = getattr(effect, "node_label", None)
            if label:
                written.setdefault(label, set()).update(effect.properties)
    return written


def test_every_property_reference_exists_on_a_model_or_is_analysis_written():
    """
    A statement that filters on a property no model declares matches nothing, and the flag
    it was meant to set then reads "clean" for every node. This is how the guest-isolation
    job silently never marked a single client: it compared ``c.wlanconf_id``, which the
    UnifiClient model does not define.
    """
    declared = _declared_properties()
    written = _written_properties()
    unknown: list[str] = []

    for job in UNIFI_ANALYSIS_JOBS:
        for statement in job.statements:
            assert statement.match is not None
            aliases = _alias_labels(statement.match)
            for alias, prop in _PROPERTY_REF.findall(statement.match):
                label = aliases.get(alias)
                if label is None:
                    continue
                if prop in declared.get(label, set()) or prop in written.get(
                    label, set()
                ):
                    continue
                unknown.append(f"{job.short_name}: {label}.{prop}")

    assert unknown == []


def test_all_jobs_are_scoped_to_the_site_being_synced():
    """
    Unscoped jobs joined nodes from different sites and their cleanup wiped every other
    site's flags on every run.
    """
    for job in UNIFI_ANALYSIS_JOBS:
        assert job.scope is not None, job.short_name
        assert job.scope.label == "UnifiSite"
        assert job.scope.id_param == "site_id"

    for job in UNIFI_ANALYSIS_JOBS:
        for statement in to_graph_job(job).statements:
            assert "(scope:UnifiSite {id: $site_id})" in statement.query


def test_guest_isolation_cleanup_covers_every_label_it_writes():
    """
    The JSON predecessor removed its flags from UnifiWlan only, so ``guest_isolated`` and
    ``guest_isolation_issues`` on UnifiClient, once set, persisted across every later sync.
    """
    cleanup_labels = {
        effect.node_label for effect in properties_set(UNIFI_GUEST_ISOLATION)
    }
    assert {"UnifiWlan", "UnifiClient", "UnifiVoucher"} == cleanup_labels

    statements = to_graph_job(UNIFI_GUEST_ISOLATION).statements
    removals = [s.query for s in statements if "REMOVE" in s.query]
    assert any(
        "UnifiClient" in q and "guest_isolated" in q for q in removals
    ), "client isolation flag is never reset"
    assert any(
        "UnifiClient" in q and "guest_isolation_issues" in q for q in removals
    ), "client isolation issues are never reset"


def test_guest_isolation_resolves_clients_through_the_wlan_relationship():
    """
    The client-to-WLAN link exists as CONNECTED_TO_WLAN, which is built from the row-level
    wlanconf_id. Traversing it is the only way to reach the WLAN from a client, since the
    client model never stores that id as a property.
    """
    matches = " ".join(s.match or "" for s in UNIFI_GUEST_ISOLATION.statements)
    assert "wlanconf_id" not in matches
    assert "(c:UnifiClient)-[:CONNECTED_TO_WLAN]->(w:UnifiWlan)" in matches


def test_no_job_traverses_resource_from_a_child_to_its_site():
    """
    RESOURCE always runs (:UnifiSite)->(:Unifi*). A statement written the other way round
    parses fine and matches nothing.
    """
    for job in UNIFI_ANALYSIS_JOBS:
        for statement in job.statements:
            assert statement.match is not None
            assert not re.search(
                r"\(\s*\w+\s*:\s*Unifi(?!Site)\w+[^)]*\)\s*-\[:RESOURCE\]->\s*\(\s*\w+\s*:\s*UnifiSite",
                statement.match,
            ), f"{job.short_name} traverses RESOURCE backwards"


def test_guest_isolation_issues_is_always_a_list():
    """
    The predecessor assigned a bare string on UnifiClient while using a list on UnifiWlan,
    leaving the same property with two types graph-wide.
    """
    for statement in to_graph_job(UNIFI_GUEST_ISOLATION).statements:
        if "guest_isolation_issues" not in statement.query or "SET" not in (
            statement.query
        ):
            continue
        # The list-append form the AddToSet effect compiles to.
        assert "IS NULL THEN [" in statement.query


def test_poor_power_factor_requires_a_positive_power_reading():
    """
    An idle metered outlet reports a power factor of 0, so without a load check the finding
    fires on every unused outlet -- six of ten flagged rows in the reference deployment.
    """
    power_factor_statements = [
        s.match
        for s in UNIFI_POWER_MONITORING.statements
        if s.match and "power_factor" in s.match
    ]
    assert len(power_factor_statements) == 1
    assert "toFloat(o.power) > 0" in power_factor_statements[0]


def test_speedtest_without_metrics_is_not_scored_as_excellent():
    """
    Every threshold comparison against NULL is NULL, so a speedtest that returned no
    figures fell through to the empty-issues default and scored 100 "excellent".
    """
    matches = [s.match for s in UNIFI_WAN_PERFORMANCE.statements if s.match]
    assert any(
        "s.download IS NULL OR s.upload IS NULL OR s.ping IS NULL" in m for m in matches
    )

    score_statement = next(
        s.query
        for s in to_graph_job(UNIFI_WAN_PERFORMANCE).statements
        if "performance_score" in s.query and "SET" in s.query
    )
    # Missing metrics must yield no score at all rather than a fabricated grade.
    assert "'missing_metrics' IN coalesce(s.performance_issues, []) THEN NULL" in (
        score_statement
    )


@pytest.mark.parametrize(
    "job", UNIFI_ANALYSIS_JOBS, ids=lambda j: j.short_name or j.name
)
def test_every_job_compiles_with_cleanup_before_its_statements(job):
    """
    Generated property cleanup must run before the analysis statements; that ordering is
    what keeps a flag from surviving after the condition that set it stops holding.
    """
    statements = to_graph_job(job).statements
    removals = [i for i, s in enumerate(statements) if "REMOVE" in s.query]
    writes = [i for i, s in enumerate(statements) if "REMOVE" not in s.query]
    assert removals, job.short_name
    assert max(removals) < min(writes)


def test_client_and_device_identity_keys_include_the_site():
    """
    MAC addresses are unique per controller, not globally. Keying these two node types on
    the bare MAC made one machine seen by two controllers collapse onto a single node with
    RESOURCE edges from both sites and a site_id that changed with whichever sync ran last.
    """
    assert UnifiClientSchema().properties.id.name == "client_id"
    assert UnifiDeviceSchema().properties.id.name == "device_id"


def test_no_matcher_resolves_a_client_or_device_by_bare_mac():
    """
    A matcher left on a raw MAC field would resolve to whichever site's node happened to
    win, silently attaching the relationship to the wrong tenant's node.
    """
    offenders: list[str] = []
    for module_info in pkgutil.iter_modules(cartography.models.unifi.__path__):
        module = importlib.import_module(f"cartography.models.unifi.{module_info.name}")
        for name, attribute in vars(module).items():
            if not (
                isinstance(attribute, type)
                and issubclass(attribute, CartographyRelSchema)
                and attribute is not CartographyRelSchema
            ):
                continue
            rel = attribute()
            if rel.target_node_label not in ("UnifiClient", "UnifiDevice"):
                continue
            for field in dataclasses.fields(rel.target_node_matcher):
                prop = getattr(rel.target_node_matcher, field.name)
                if field.name == "id" and prop.name.endswith("mac"):
                    offenders.append(
                        f"{module_info.name}.{name}: {field.name}={prop.name}"
                    )

    assert offenders == []


def test_scoped_id_helpers_never_emit_a_bare_or_dangling_id():
    """
    A None MAC must stay None so the matcher simply finds nothing, rather than becoming a
    "site_None" id that could collide with a real node.
    """
    assert scoped_id("s1", "aa:bb") == "s1_aa:bb"
    assert scoped_id("s1", None) is None
    assert scoped_id("s1", "") is None
    assert scoped_ids("s1", ["aa", "bb"]) == ["s1_aa", "s1_bb"]
    assert scoped_ids("s1", None) is None
    assert scoped_ids("s1", []) is None

    rows = [{"mac": "aa", "peer_mac": None}]
    scoped = attach_scoped_ids(rows, "s1", single={"a_id": "mac", "b_id": "peer_mac"})
    assert scoped[0]["a_id"] == "s1_aa"
    assert scoped[0]["b_id"] is None
    # The raw MAC survives: several schemas expose it as a property.
    assert scoped[0]["mac"] == "aa"
    assert rows[0] == {"mac": "aa", "peer_mac": None}, "input rows must not be mutated"
