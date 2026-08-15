"""
Integration tests for OpenVAS host sync.
"""

import cartography.intel.openvas.hosts
from tests.data.openvas.responses import HOST_ID_1
from tests.data.openvas.responses import HOST_ID_2
from tests.data.openvas.responses import INSTANCE_ID
from tests.integration.cartography.intel.openvas.util import common_job_parameters
from tests.integration.cartography.intel.openvas.util import FakeGmp
from tests.integration.cartography.intel.openvas.util import seed_instance
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG
from tests.integration.cartography.intel.openvas.util import TEST_UPDATE_TAG_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_sync_hosts(neo4j_session):
    """Hosts are loaded with their properties, labels and relationships."""
    # Arrange
    seed_instance(neo4j_session)

    # Act
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert
    nodes = (
        check_nodes(
            neo4j_session,
            "OpenVASHost",
            ["id", "ip", "hostname", "os", "severity", "asset_id"],
        )
        or set()
    )
    # Node identity is the IP, not GMP's asset id -- GVM reissues asset ids
    # on every host (re)discovery, so keying on asset_id would create a new
    # duplicate node per sync instead of updating one. asset_id is kept as
    # an informational property.
    assert (
        "10.0.0.5",
        "10.0.0.5",
        "web-01.example.com",
        "Linux",
        8.1,
        HOST_ID_1,
    ) in nodes
    assert ("10.0.0.6", "10.0.0.6", None, None, 0.0, HOST_ID_2) in nodes

    # Hosts carry the DEVICE_INSTANCE semantic label.
    device_nodes = check_nodes(neo4j_session, "DeviceInstance", ["id"]) or set()
    assert ("10.0.0.5",) in device_nodes


def test_sync_hosts_dedupes_reissued_asset_ids(neo4j_session):
    """
    GVM can return several <asset> elements for the same IP in one
    get_assets response (a fresh asset id per host rediscovery). These must
    collapse into a single OpenVASHost node, keyed by IP, not accumulate.
    """
    # Arrange
    seed_instance(neo4j_session)
    gmp = FakeGmp()
    gmp._responses["get_hosts"] = f"""
    <get_assets_response status="200" status_text="OK">
      <asset_count>2<filtered>2</filtered></asset_count>
      <asset id="asset-aaa">
        <name>10.0.0.9</name>
        <identifiers>
          <identifier id="ident-a"><name>ip</name><value>10.0.0.9</value></identifier>
        </identifiers>
        <type>host</type>
        <host><severity><value>5.0</value></severity></host>
      </asset>
      <asset id="asset-bbb">
        <name>10.0.0.9</name>
        <identifiers>
          <identifier id="ident-b"><name>ip</name><value>10.0.0.9</value></identifier>
        </identifiers>
        <type>host</type>
        <host><severity><value>7.5</value></severity></host>
      </asset>
    </get_assets_response>
    """

    # Act
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        gmp,
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert: the two same-IP assets collapsed into a single node, not two.
    # (neo4j_session is module-scoped, so other tests' hosts may also be
    # present -- scope the assertion to this test's IP.)
    nodes = check_nodes(neo4j_session, "OpenVASHost", ["id", "ip"]) or set()
    matching = {n for n in nodes if n[1] == "10.0.0.9"}
    assert matching == {("10.0.0.9", "10.0.0.9")}

    check_rels(
        neo4j_session,
        "OpenVASInstance",
        "id",
        "OpenVASHost",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )


def test_sync_hosts_cleanup_stale(neo4j_session):
    """Hosts not seen in a newer sync are removed scoped to the instance."""
    # Arrange
    seed_instance(neo4j_session)

    # Act
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        FakeGmp(),
        INSTANCE_ID,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )
    stale_gmp = FakeGmp()
    # A sync with no hosts returned: both hosts must be cleaned up.
    stale_gmp._responses["get_hosts"] = (
        '<get_assets_response status="200" status_text="OK">'
        "<asset_count>0<filtered>0</filtered></asset_count>"
        "</get_assets_response>"
    )
    cartography.intel.openvas.hosts.sync_hosts(
        neo4j_session,
        stale_gmp,
        INSTANCE_ID,
        TEST_UPDATE_TAG_2,
        {**common_job_parameters(), "UPDATE_TAG": TEST_UPDATE_TAG_2},
    )

    # Assert
    assert not check_nodes(neo4j_session, "OpenVASHost", ["id"])
