"""
Mock data for Proxmox authentication realm tests.
"""

# Mock authentication realm data
MOCK_AUTH_REALM_DATA = [
    {
        "realm": "pam",
        "type": "pam",
        "comment": "Linux PAM standard authentication",
        "default": 1,
    },
    {
        "realm": "pve",
        "type": "pve",
        "comment": "Proxmox VE authentication server",
        "default": 0,
    },
    {
        "realm": "ldap-corp",
        "type": "ldap",
        "comment": "Corporate LDAP directory",
        "default": 0,
        "tfa": "oath",
    },
    {
        "realm": "ad-domain",
        "type": "ad",
        "comment": "Active Directory authentication",
        "default": 0,
    },
]

# Expected transformed auth realms for cluster1
MOCK_AUTH_REALMS_TRANSFORMED = [
    {
        "id": "cluster1:pam",
        "realm": "pam",
        "cluster_id": "cluster1",
        "type": "pam",
        "comment": "Linux PAM standard authentication",
        "default": True,
        "tfa": None,
    },
    {
        "id": "cluster1:pve",
        "realm": "pve",
        "cluster_id": "cluster1",
        "type": "pve",
        "comment": "Proxmox VE authentication server",
        "default": False,
        "tfa": None,
    },
    {
        "id": "cluster1:ldap-corp",
        "realm": "ldap-corp",
        "cluster_id": "cluster1",
        "type": "ldap",
        "comment": "Corporate LDAP directory",
        "default": False,
        "tfa": "oath",
    },
    {
        "id": "cluster1:ad-domain",
        "realm": "ad-domain",
        "cluster_id": "cluster1",
        "type": "ad",
        "comment": "Active Directory authentication",
        "default": False,
        "tfa": None,
    },
]
