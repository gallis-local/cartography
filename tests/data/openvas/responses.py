"""
Mock GMP (Greenbone Management Protocol) responses for OpenVAS intel tests.

Each response mirrors the XML shape emitted by gvmd for the corresponding
get_* command, wrapped in its <get_*_response> root element.
"""

from xml.etree import ElementTree

INSTANCE_ID = "gvm.example.com:9390"

HOST_ID_1 = "11111111-1111-1111-1111-111111111111"
HOST_ID_2 = "22222222-2222-2222-2222-222222222222"
TASK_ID_1 = "33333333-3333-3333-3333-333333333333"
TASK_ID_2 = "44444444-4444-4444-4444-444444444444"
TARGET_ID_1 = "55555555-5555-5555-5555-555555555555"
CONFIG_ID_1 = "66666666-6666-6666-6666-666666666666"
SCHEDULE_ID_1 = "77777777-7777-7777-7777-777777777777"
PORT_LIST_ID_1 = "88888888-8888-8888-8888-888888888888"
SSH_CRED_ID_1 = "99999999-9999-9999-9999-999999999999"
SMB_CRED_ID_1 = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
RESULT_ID_1 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
RESULT_ID_2 = "cccccccc-cccc-cccc-cccc-cccccccccccc"
NVT_OID_1 = "1.3.6.1.4.1.25623.1.0.100001"
NVT_OID_2 = "1.3.6.1.4.1.25623.1.0.100002"
CERT_ID_1 = "dddddddd-dddd-dddd-dddd-dddddddddddd"
CERT_ID_2 = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"

GET_HOSTS_RESPONSE = f"""
<get_hosts_response status="200" status_text="OK">
  <host_count>2</host_count>
  <host id="{HOST_ID_1}">
    <name>10.0.0.5</name>
    <comment>web server</comment>
    <creation_time>2024-01-01T00:00:00+00:00</creation_time>
    <modification_time>2024-06-01T00:00:00+00:00</modification_time>
    <hostname>web-01.example.com</hostname>
    <ip>10.0.0.5</ip>
    <os>Linux</os>
    <asset id="asset-1"/>
    <severity>8.1</severity>
    <latest_scan>
      <date>2024-06-01T12:00:00+00:00</date>
      <task id="{TASK_ID_1}"><name>Full Scan</name></task>
    </latest_scan>
    <source_type>scan</source_type>
    <identifiers>ip: 10.0.0.5</identifiers>
  </host>
  <host id="{HOST_ID_2}">
    <name>10.0.0.6</name>
    <ip>10.0.0.6</ip>
    <severity>0.0</severity>
  </host>
</get_hosts_response>
"""

GET_TASKS_RESPONSE = f"""
<get_tasks_response status="200" status_text="OK">
  <task_count>2</task_count>
  <task id="{TASK_ID_1}">
    <name>Full Scan</name>
    <comment>weekly full scan</comment>
    <creation_time>2024-01-01T00:00:00+00:00</creation_time>
    <modification_time>2024-06-01T00:00:00+00:00</modification_time>
    <alterable>0</alterable>
    <status>Done</status>
    <target id="{TARGET_ID_1}"><name>Prod Network</name></target>
    <config id="{CONFIG_ID_1}"><name>Full and fast</name></config>
    <schedule id="{SCHEDULE_ID_1}"><name>Weekly</name></schedule>
    <last_report id="report-1">
      <timestamp>2024-06-01T12:00:00+00:00</timestamp>
      <severity>8.1</severity>
      <scan_start>2024-06-01T10:00:00+00:00</scan_start>
      <scan_end>2024-06-01T12:00:00+00:00</scan_end>
    </last_report>
  </task>
  <task id="{TASK_ID_2}">
    <name>Quick Scan</name>
    <status>Running</status>
    <target id="{TARGET_ID_1}"><name>Prod Network</name></target>
    <config id="{CONFIG_ID_1}"><name>Full and fast</name></config>
  </task>
</get_tasks_response>
"""

GET_TARGETS_RESPONSE = f"""
<get_targets_response status="200" status_text="OK">
  <target_count>1</target_count>
  <target id="{TARGET_ID_1}">
    <name>Prod Network</name>
    <comment>production subnets</comment>
    <creation_time>2024-01-01T00:00:00+00:00</creation_time>
    <modification_time>2024-06-01T00:00:00+00:00</modification_time>
    <hosts>10.0.0.0/24</hosts>
    <max_hosts>254</max_hosts>
    <exclude_hosts>10.0.0.254</exclude_hosts>
    <port_list id="{PORT_LIST_ID_1}"><name>All IANA assigned TCP</name></port_list>
    <alive_test>ICMP Ping</alive_test>
    <allow_simultaneous_ips>0</allow_simultaneous_ips>
    <reverse_lookup_only>0</reverse_lookup_only>
    <reverse_lookup_unify>0</reverse_lookup_unify>
    <ssh_credential id="{SSH_CRED_ID_1}"/>
    <smb_credential id="{SMB_CRED_ID_1}"/>
  </target>
</get_targets_response>
"""

GET_CONFIGS_RESPONSE = f"""
<get_configs_response status="200" status_text="OK">
  <config_count>1</config_count>
  <config id="{CONFIG_ID_1}">
    <name>Full and fast</name>
    <comment>default config</comment>
    <creation_time>2024-01-01T00:00:00+00:00</creation_time>
    <modification_time>2024-06-01T00:00:00+00:00</modification_time>
    <config_type>0</config_type>
    <usage_type>scan</usage_type>
    <family_count>60</family_count>
    <nvt_count>1000</nvt_count>
  </config>
</get_configs_response>
"""

GET_SCHEDULES_RESPONSE = f"""
<get_schedules_response status="200" status_text="OK">
  <schedule_count>1</schedule_count>
  <schedule id="{SCHEDULE_ID_1}">
    <name>Weekly</name>
    <comment>every monday</comment>
    <creation_time>2024-01-01T00:00:00+00:00</creation_time>
    <modification_time>2024-06-01T00:00:00+00:00</modification_time>
    <timezone>UTC</timezone>
    <icalendar>BEGIN:VCALENDAR...</icalendar>
    <next_run>2024-06-08T00:00:00+00:00</next_run>
  </schedule>
</get_schedules_response>
"""

GET_PORT_LISTS_RESPONSE = f"""
<get_port_lists_response status="200" status_text="OK">
  <port_list_count>1</port_list_count>
  <port_list id="{PORT_LIST_ID_1}">
    <name>All IANA assigned TCP</name>
    <comment>standard list</comment>
    <creation_time>2024-01-01T00:00:00+00:00</creation_time>
    <modification_time>2024-06-01T00:00:00+00:00</modification_time>
    <port_count>1024</port_count>
  </port_list>
</get_port_lists_response>
"""

GET_CREDENTIALS_RESPONSE = f"""
<get_credentials_response status="200" status_text="OK">
  <credential_count>2</credential_count>
  <credential id="{SSH_CRED_ID_1}">
    <name>prod ssh</name>
    <comment>ssh key</comment>
    <creation_time>2024-01-01T00:00:00+00:00</creation_time>
    <modification_time>2024-06-01T00:00:00+00:00</modification_time>
    <type>up</type>
    <allow_insecure>0</allow_insecure>
  </credential>
  <credential id="{SMB_CRED_ID_1}">
    <name>win smb</name>
    <type>smb</type>
    <allow_insecure>1</allow_insecure>
  </credential>
</get_credentials_response>
"""

GET_RESULTS_RESPONSE = f"""
<get_results_response status="200" status_text="OK">
  <result_count full="1" truncated="0">2</result_count>
  <result id="{RESULT_ID_1}">
    <name>Apache mod_negotiation</name>
    <host>10.0.0.5</host>
    <hostname>web-01.example.com</hostname>
    <port>80/tcp</port>
    <nvt id="{NVT_OID_1}" oid="{NVT_OID_1}">
      <name>Apache mod_negotiation</name>
      <cvss_base>7.5</cvss_base>
      <cve>CVE-2024-1000</cve>
      <family>Web Servers</family>
      <severity>High</severity>
      <solution type="VendorFix">Upgrade Apache.</solution>
      <qod value="70" type="remote_banner"/>
      <refs>
        <ref type="cve" id="CVE-2024-1000"/>
        <ref type="url" id="https://example.com/advisory"/>
      </refs>
      <tags>cvss_base_vector=AV:N/AC:L/Au:N/C:P/I:P/A:P;summary=summary text;detection_result=detected</tags>
    </nvt>
    <severity>7.5</severity>
    <qod value="70" type="remote_banner"/>
    <threat>High</threat>
    <original_threat>High</original_threat>
    <description>Apache mod_negotiation is enabled.</description>
    <task id="{TASK_ID_1}"><name>Full Scan</name></task>
    <source_ip>10.0.0.1</source_ip>
    <asset asset_id="asset-1"/>
    <created>2024-06-01T12:05:00+00:00</created>
  </result>
  <result id="{RESULT_ID_2}">
    <name>TCP timestamps</name>
    <host>10.0.0.6</host>
    <port>general/tcp</port>
    <nvt id="{NVT_OID_2}" oid="{NVT_OID_2}">
      <name>TCP timestamps</name>
      <cvss_base>0.0</cvss_base>
      <family>General</family>
      <severity>Log</severity>
      <qod value="80" type="remote_active"/>
      <tags>summary=info only</tags>
    </nvt>
    <severity>0.0</severity>
    <qod value="80" type="remote_active"/>
    <threat>Log</threat>
    <original_threat>Log</original_threat>
    <description>TCP timestamps are enabled.</description>
    <task id="{TASK_ID_2}"><name>Quick Scan</name></task>
    <created>2024-06-02T10:00:00+00:00</created>
  </result>
</get_results_response>
"""

GET_TLS_CERTIFICATES_RESPONSE = f"""
<get_tls_certificates_response status="200" status_text="OK">
  <tls_certificate_count>2</tls_certificate_count>
  <tls_certificate id="{CERT_ID_1}">
    <name>10.0.0.5</name>
    <subject>CN=web-01.example.com</subject>
    <issuer>CN=Example Root CA</issuer>
    <not_before>2024-01-01T00:00:00+00:00</not_before>
    <not_after>2025-01-01T00:00:00+00:00</not_after>
    <serial>0x1234</serial>
    <fingerprint>aa:bb:cc</fingerprint>
    <certificate_format>PEM</certificate_format>
    <key_type>RSA</key_type>
    <key_bits>2048</key_bits>
    <activation_time>2024-01-01T00:00:00+00:00</activation_time>
    <expiry_time>2025-01-01T00:00:00+00:00</expiry_time>
    <source_type>scan</source_type>
    <status>valid</status>
  </tls_certificate>
  <tls_certificate id="{CERT_ID_2}">
    <name>10.0.0.99</name>
    <subject>CN=unknown-host</subject>
    <issuer>CN=Example Root CA</issuer>
    <not_after>2025-06-01T00:00:00+00:00</not_after>
  </tls_certificate>
</get_tls_certificates_response>
"""


def parse(response_xml: str) -> ElementTree.Element:
    """Parse a response XML string into an ElementTree element."""
    return ElementTree.fromstring(response_xml)
