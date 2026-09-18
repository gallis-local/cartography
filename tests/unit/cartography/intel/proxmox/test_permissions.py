"""
Tests for the derived Proxmox permission relationships.
"""

from cartography.intel.proxmox.access import transform_acl_data
from cartography.intel.proxmox.access import transform_effective_permissions
from cartography.intel.proxmox.access import transform_role_data
from cartography.intel.proxmox.access import transform_user_data
from cartography.intel.proxmox.access import transform_user_role_links
from tests.data.proxmox.access import MOCK_ACL_DATA
from tests.data.proxmox.access import MOCK_GROUP_MEMBERS_DATA
from tests.data.proxmox.access import MOCK_ROLE_DATA
from tests.data.proxmox.access import MOCK_USER_DATA

CLUSTER_ID = "test-cluster"


def _fixtures():
    acls = transform_acl_data(MOCK_ACL_DATA, CLUSTER_ID)
    users = transform_user_data(MOCK_USER_DATA, CLUSTER_ID, MOCK_GROUP_MEMBERS_DATA)
    roles = transform_role_data(MOCK_ROLE_DATA, CLUSTER_ID)
    return acls, users, roles


def _find(rows, principal_id, resource_id):
    for row in rows:
        if row["principal_id"] == principal_id and row["resource_id"] == resource_id:
            return row
    return None


def test_cluster_grants_resolve_for_users_and_groups():
    """Root-path ACLs produce edges to the cluster for both principal types."""
    acls, users, roles = _fixtures()

    result = transform_effective_permissions(acls, users, roles, CLUSTER_ID)

    user_rows = result[("cluster", "user")]
    group_rows = result[("cluster", "group")]

    # The direct "/" grant to root@pam.
    root = _find(user_rows, f"{CLUSTER_ID}/user/root@pam", CLUSTER_ID)
    assert root is not None
    assert "Administrator" in root["roles"]

    # The "/" grant to the admins group.
    admins = _find(group_rows, f"{CLUSTER_ID}/group/admins", CLUSTER_ID)
    assert admins is not None
    assert admins["roles"] == ["Administrator"]
    assert admins["via_group"] is False


def test_group_grants_are_inherited_by_members():
    """A group's grant becomes an effective grant for each member, flagged via_group."""
    acls, users, roles = _fixtures()

    result = transform_effective_permissions(acls, users, roles, CLUSTER_ID)
    user_rows = result[("cluster", "user")]

    # admin@pve holds no direct "/" ACL; it only belongs to the admins group.
    admin = _find(user_rows, f"{CLUSTER_ID}/user/admin@pve", CLUSTER_ID)
    assert admin is not None
    assert admin["roles"] == ["Administrator"]
    assert admin["via_group"] is True


def test_privileges_are_expanded_from_the_granted_role():
    """Role privileges are copied onto the edge so queries need not join to the role."""
    acls, users, roles = _fixtures()

    result = transform_effective_permissions(acls, users, roles, CLUSTER_ID)
    admins = _find(
        result[("cluster", "group")], f"{CLUSTER_ID}/group/admins", CLUSTER_ID
    )

    assert "Sys.Modify" in admins["privileges"]
    assert "Datastore.Allocate" in admins["privileges"]


def test_vm_grant_carries_an_integer_vmid_for_matching():
    """ProxmoxVM.vmid is an int, so the match key must be an int, not a string."""
    acls, users, roles = _fixtures()

    result = transform_effective_permissions(acls, users, roles, CLUSTER_ID)
    vm_rows = result[("vm", "user")]

    row = _find(vm_rows, f"{CLUSTER_ID}/user/readonly@pam", "100")
    assert row is not None
    assert row["resource_id_int"] == 100
    assert row["roles"] == ["CustomRole"]


def test_storage_grant_resolves_to_the_storage_name():
    acls, users, roles = _fixtures()

    result = transform_effective_permissions(acls, users, roles, CLUSTER_ID)
    row = _find(
        result[("storage", "group")], f"{CLUSTER_ID}/group/auditors", "local-lvm"
    )

    assert row is not None
    assert row["roles"] == ["PVEAuditor"]


def test_paths_without_a_resource_id_are_skipped():
    """ "/vms" and "/access" name no specific resource, so they yield no edge."""
    acls, users, roles = _fixtures()

    result = transform_effective_permissions(acls, users, roles, CLUSTER_ID)

    # "/vms" parses to an unknown resource type; nothing should be emitted for it.
    for rows in result.values():
        for row in rows:
            assert row["paths"] != ["/vms"]


def test_multiple_grants_on_one_pair_accumulate_instead_of_overwriting():
    """
    Two roles on the same (principal, resource) pair must both survive.

    Only one graph edge can exist between the pair, so the roles are aggregated. An
    implementation that overwrote properties per ACL would silently lose a grant.
    """
    acls = transform_acl_data(
        MOCK_ACL_DATA
        + [
            # A second, different role for readonly@pam on the same VM.
            {
                "path": "/vms/100",
                "roleid": "PVEAuditor",
                "ugid": "readonly@pam",
                "propagate": 1,
            },
        ],
        CLUSTER_ID,
    )
    users = transform_user_data(MOCK_USER_DATA, CLUSTER_ID, MOCK_GROUP_MEMBERS_DATA)
    roles = transform_role_data(MOCK_ROLE_DATA, CLUSTER_ID)

    result = transform_effective_permissions(acls, users, roles, CLUSTER_ID)
    row = _find(result[("vm", "user")], f"{CLUSTER_ID}/user/readonly@pam", "100")

    assert sorted(row["roles"]) == ["CustomRole", "PVEAuditor"]
    # propagate=1 on either contributing ACL makes the effective grant propagating.
    assert row["propagate"] is True
    # Privileges from both roles are present.
    assert "VM.PowerMgmt" in row["privileges"]
    assert "VM.Audit" in row["privileges"]


def test_api_token_principals_get_no_permission_edge():
    """
    Tokens inherit their user's permissions in Proxmox and are modelled separately.
    """
    acls = transform_acl_data(
        [
            {
                "path": "/",
                "roleid": "PVEAuditor",
                "ugid": "root@pam!cartography",
                "propagate": 1,
            },
        ],
        CLUSTER_ID,
    )
    users = transform_user_data(MOCK_USER_DATA, CLUSTER_ID, MOCK_GROUP_MEMBERS_DATA)
    roles = transform_role_data(MOCK_ROLE_DATA, CLUSTER_ID)

    result = transform_effective_permissions(acls, users, roles, CLUSTER_ID)

    assert result == {}


def test_user_role_links_collect_every_path():
    """A user holding one role on several paths keeps all of them on one edge."""
    acls = transform_acl_data(
        [
            {
                "path": "/vms/100",
                "roleid": "PVEAuditor",
                "ugid": "readonly@pam",
                "propagate": 1,
            },
            {
                "path": "/storage/local-lvm",
                "roleid": "PVEAuditor",
                "ugid": "readonly@pam",
                "propagate": 0,
            },
        ],
        CLUSTER_ID,
    )
    users = transform_user_data(MOCK_USER_DATA, CLUSTER_ID, MOCK_GROUP_MEMBERS_DATA)

    rows = transform_user_role_links(acls, users, CLUSTER_ID)

    assert len(rows) == 1
    assert rows[0]["principal_id"] == f"{CLUSTER_ID}/user/readonly@pam"
    assert rows[0]["roleid"] == "PVEAuditor"
    assert sorted(rows[0]["paths"]) == ["/storage/local-lvm", "/vms/100"]


def test_user_role_links_include_roles_inherited_from_groups():
    acls = transform_acl_data(
        [
            {
                "path": "/",
                "roleid": "Administrator",
                "ugid": "admins",
                "propagate": 1,
            },
        ],
        CLUSTER_ID,
    )
    users = transform_user_data(MOCK_USER_DATA, CLUSTER_ID, MOCK_GROUP_MEMBERS_DATA)

    rows = transform_user_role_links(acls, users, CLUSTER_ID)
    by_principal = {r["principal_id"]: r for r in rows}

    # Both admins members inherit the role, and it is flagged as group-derived.
    assert f"{CLUSTER_ID}/user/root@pam" in by_principal
    assert f"{CLUSTER_ID}/user/admin@pve" in by_principal
    assert by_principal[f"{CLUSTER_ID}/user/admin@pve"]["via_group"] is True
