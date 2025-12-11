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
        "site_id": "default",
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
        "site_id": "default",
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
        "site_id": "default",
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
        "site_id": "default",
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
        "site_id": "default",
    },
]

# Test data for UniFi port forwards
UNIFI_PORT_FORWARDS = [
    {
        "id": "pf_001",
        "name": "Web Server",
        "enabled": True,
        "destination_port": "80",
        "forward_port": "8080",
        "forward_ip": "192.168.1.50",
        "protocol": "tcp",
        "interface": "wan",
        "source": "any",
        "site_id": "default",
    },
    {
        "id": "pf_002",
        "name": "SSH Server",
        "enabled": False,
        "destination_port": "22",
        "forward_port": "2222",
        "forward_ip": "192.168.1.51",
        "protocol": "tcp",
        "interface": "wan",
        "source": "192.168.1.0/24",
        "site_id": "default",
    },
]

# Test data for UniFi traffic rules
UNIFI_TRAFFIC_RULES = [
    {
        "id": "tr_001",
        "description": "Block Social Media",
        "enabled": True,
        "action": "BLOCK",
        "matching_target": "INTERNET",
        "bandwidth_limit_enabled": False,
        "download_limit_kbps": None,
        "upload_limit_kbps": None,
        "site_id": "default",
    },
    {
        "id": "tr_002",
        "description": "Limit Guest Bandwidth",
        "enabled": True,
        "action": "ALLOW",
        "matching_target": "INTERNET",
        "bandwidth_limit_enabled": True,
        "download_limit_kbps": 10240,
        "upload_limit_kbps": 2048,
        "site_id": "default",
    },
]

# Test data for UniFi traffic routes
UNIFI_TRAFFIC_ROUTES = [
    {
        "id": "route_001",
        "description": "VPN Route",
        "enabled": True,
        "matching_target": "IP",
        "network_id": "network_001",
        "next_hop": "192.168.1.1",
        "site_id": "default",
    },
]

# Test data for UniFi DPI groups
UNIFI_DPI_GROUPS = [
    {
        "id": "dpi_group_001",
        "name": "Restricted Apps",
        "attr_no_delete": False,
        "attr_hidden_id": "",
        "site_id": "default",
    },
    {
        "id": "dpi_group_002",
        "name": "Default",
        "attr_no_delete": True,
        "attr_hidden_id": "Default",
        "site_id": "default",
    },
]

# Test data for UniFi DPI apps
UNIFI_DPI_APPS = [
    {
        "id": "dpi_app_001",
        "blocked": True,
        "enabled": True,
        "log": True,
        "site_id": "default",
        "dpi_group_ids": ["dpi_group_001"],
    },
    {
        "id": "dpi_app_002",
        "blocked": False,
        "enabled": True,
        "log": False,
        "site_id": "default",
        "dpi_group_ids": None,
    },
]

# Test data for UniFi firewall policies
UNIFI_FIREWALL_POLICIES = [
    {
        "id": "fw_policy_001",
        "name": "Allow LAN to WAN",
        "description": "Allow all LAN traffic to WAN",
        "enabled": True,
        "action": "ALLOW",
        "protocol": "all",
        "predefined": False,
        "index": 1,
        "connection_state_type": "ALL",
        "logging": False,
        "site_id": "default",
    },
    {
        "id": "fw_policy_002",
        "name": "Block Guest to LAN",
        "description": "Prevent guest network from accessing LAN",
        "enabled": True,
        "action": "DENY",
        "protocol": "all",
        "predefined": False,
        "index": 2,
        "connection_state_type": "NEW",
        "logging": True,
        "site_id": "default",
    },
]

# Test data for UniFi firewall zones
UNIFI_FIREWALL_ZONES = [
    {
        "id": "fw_zone_001",
        "name": "LAN",
        "attr_no_edit": True,
        "default_zone": True,
        "zone_key": "lan",
        "network_ids": ["network_001", "network_002"],
        "site_id": "default",
    },
    {
        "id": "fw_zone_002",
        "name": "WAN",
        "attr_no_edit": True,
        "default_zone": True,
        "zone_key": "wan",
        "network_ids": ["network_wan"],
        "site_id": "default",
    },
]

# Test data for UniFi vouchers
UNIFI_VOUCHERS = [
    {
        "id": "voucher_001",
        "code": "12345-67890",
        "note": "Conference attendees",
        "quota": 100,
        "duration": 480,
        "qos_overwrite": True,
        "qos_usage_quota": 1024,
        "qos_rate_max_up": 5000,
        "qos_rate_max_down": 10000,
        "used": 15,
        "create_time": 1638342818,
        "start_time": 1638342900,
        "end_time": 1638371700,
        "for_hotspot": False,
        "admin_name": "admin",
        "status": "VALID_MULTI",
        "status_expires": 1640934818,
        "site_id": "default",
    },
    {
        "id": "voucher_002",
        "code": "98765-43210",
        "note": "Guest WiFi",
        "quota": 0,
        "duration": 1440,
        "qos_overwrite": False,
        "qos_usage_quota": None,
        "qos_rate_max_up": None,
        "qos_rate_max_down": None,
        "used": 2,
        "create_time": 1638428818,
        "start_time": None,
        "end_time": None,
        "for_hotspot": True,
        "admin_name": "admin",
        "status": "USED_MULTIPLE",
        "status_expires": None,
        "site_id": "default",
    },
]

# Test data for UniFi system information
UNIFI_SYSTEM_INFO = [
    {
        "id": "controller_001",
        "anonymous_controller_id": "24f81231-a456-4c32-abcd-f5612345385f",
        "hostname": "unifi-controller",
        "name": "UniFi Controller",
        "version": "7.4.162",
        "previous_version": "7.3.83",
        "update_available": True,
        "ip_addrs": ["192.168.1.1", "10.0.0.1"],
        "is_cloud_console": False,
        "ubnt_device_type": "UDM-Pro",
        "site_id": "default",
    },
]
