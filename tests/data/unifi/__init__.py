# Test data for UniFi sites
UNIFI_SITES = [
    {
        "_id": "default",
        "name": "Default",
        "desc": "Default Site",
        "role": "admin",
    },
]

# Test data for UniFi devices
UNIFI_DEVICES = [
    {
        "mac": "00:11:22:33:44:55",
        "adopted": True,
        "type": "uap",
        "model": "U7PG2",
        "name": "Office AP",
        "site_id": "default",
    },
    {
        "mac": "AA:BB:CC:DD:EE:FF",
        "adopted": True,
        "type": "usw",
        "model": "US24P250",
        "name": "Main Switch",
        "site_id": "default",
    },
]

# Test data for UniFi WLANs
UNIFI_WLANS = [
    {
        "_id": "wlan_001",
        "name": "Corporate WiFi",
        "enabled": True,
        "is_guest": False,
        "security": "wpapsk",
        "wpa_mode": "wpa2",
        "wpa_enc": "ccmp",
        "usergroup_id": None,
        "hide_ssid": False,
        "mac_filter_enabled": False,
        "site_id": "default",
    },
    {
        "_id": "wlan_002",
        "name": "Guest WiFi",
        "enabled": True,
        "is_guest": True,
        "security": "open",
        "wpa_mode": None,
        "wpa_enc": None,
        "usergroup_id": "guest",
        "hide_ssid": False,
        "mac_filter_enabled": False,
        "site_id": "default",
    },
]

# Test data for UniFi ports
UNIFI_PORTS = [
    {
        "id": "AA:BB:CC:DD:EE:FF:1",
        "port_idx": 1,
        "name": "Port 1",
        "port_poe": True,
        "poe_enable": True,
        "poe_mode": "auto",
        "poe_voltage": 48.0,
        "portconf_id": "port_profile_001",
        "up": True,
        "speed": 1000,
        "full_duplex": True,
        "device_mac": "AA:BB:CC:DD:EE:FF",
    },
    {
        "id": "AA:BB:CC:DD:EE:FF:2",
        "port_idx": 2,
        "name": "Port 2",
        "port_poe": True,
        "poe_enable": False,
        "poe_mode": None,
        "poe_voltage": None,
        "portconf_id": "port_profile_002",
        "up": False,
        "speed": 0,
        "full_duplex": False,
        "device_mac": "AA:BB:CC:DD:EE:FF",
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
