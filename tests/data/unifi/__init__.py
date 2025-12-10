# Test data for UniFi devices
UNIFI_DEVICES = [
    {
        "mac": "00:11:22:33:44:55",
        "adopted": True,
        "type": "uap",
        "model": "U7PG2",
        "name": "Office AP",
    },
    {
        "mac": "AA:BB:CC:DD:EE:FF",
        "adopted": True,
        "type": "usw",
        "model": "US24P250",
        "name": "Main Switch",
    },
]

# Test data for UniFi clients
UNIFI_CLIENTS = [
    {
        "mac": "11:22:33:44:55:66",
        "ip": "192.168.1.100",
        "is_guest": False,
        "oui": "Apple",
        "satisfaction": 98,
        "channel": 36,
        "radio": "ng",
        "is_wired": False,
        "qos_policy_applied": False,
        "ap_mac": "00:11:22:33:44:55",
    },
    {
        "mac": "77:88:99:AA:BB:CC",
        "ip": "192.168.1.101",
        "is_guest": True,
        "oui": "Samsung",
        "satisfaction": 85,
        "channel": 149,
        "radio": "na",
        "is_wired": False,
        "qos_policy_applied": True,
        "ap_mac": "00:11:22:33:44:55",
    },
    {
        "mac": "DD:EE:FF:00:11:22",
        "ip": "192.168.1.102",
        "is_guest": False,
        "oui": "Dell",
        "satisfaction": 100,
        "channel": None,
        "radio": None,
        "is_wired": True,
        "qos_policy_applied": False,
        "ap_mac": "AA:BB:CC:DD:EE:FF",
    },
]
