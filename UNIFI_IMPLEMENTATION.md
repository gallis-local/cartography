# UniFi Intel Module - Implementation Analysis & Recommendations

## ✅ Current Implementation (Updated to aiounifi)

The UniFi module has been **migrated to use aiounifi** (v81+), an actively maintained async library for UniFi Controller API access.

### Architecture

**Components:**
- `cartography/models/unifi/` - Data models for UnifiSite, UnifiDevice, UnifiWlan, UnifiPort, and UnifiClient nodes
- `cartography/intel/unifi/` - Async intel modules for syncing all UniFi objects
- `tests/data/unifi/` - Test fixtures with sample data
- `tests/integration/cartography/intel/unifi/` - Async integration tests
- `tests/unit/cartography/intel/unifi/` - Async unit tests

**Graph Schema:**
```
(UnifiDevice)-[:RESOURCE]->(UnifiSite)
(UnifiWlan)-[:RESOURCE]->(UnifiSite)
(UnifiPort)-[:HAS_PORT]->(UnifiDevice)
(UnifiClient)-[:RESOURCE]->(UnifiDevice)
```

## Library Migration Complete ✅

### From unificontrol to aiounifi

**Previous:** `unificontrol>=0.3.3` (unmaintained since Jan 2021)
**Current:** `aiounifi>=81` (actively maintained, latest Dec 2024)

### Benefits of Migration

1. **Active Maintenance** - Regular updates throughout 2024
2. **Security** - Receives timely security patches
3. **Compatibility** - Keeps pace with UniFi Controller API changes
4. **Performance** - Async I/O for better scalability
5. **Community** - Large user base via Home Assistant
6. **Future-proof** - Python 3.13+ support

## Implementation Details

### Async Pattern

The module uses Cartography's standard async pattern:

```python
# Main entry point is synchronous
def start_unifi_ingestion(neo4j_session, config):
    asyncio.run(_sync_unifi(...))

# Internal implementation is async
async def _sync_unifi(...):
    controller = await create_unifi_controller(...)
    try:
        await devices.sync(...)
        await clients.sync(...)
    finally:
        await close_controller(controller)
```

### Key Features

1. **Site Tracking**: Discovers and tracks UniFi sites
   - Multi-site deployments
   - Site descriptions and roles
   - Organization hierarchy

2. **Device Tracking**: Discovers and tracks UniFi network devices
   - Access Points (UAPs)
   - Switches (USW)
   - Other adopted devices
   - Device-to-site relationships

3. **WLAN Tracking**: Monitors wireless network configurations
   - SSID configurations
   - Security settings (WPA2, WPA3, Open)
   - Guest vs. corporate networks
   - Hidden SSIDs and MAC filtering

4. **Port Tracking**: Tracks switch port configurations
   - PoE capabilities and status
   - Port speeds and duplex settings
   - Connectivity status
   - Port profiles

5. **Client Tracking**: Monitors connected clients
   - Wireless and wired clients
   - Guest vs. regular clients
   - Connection quality metrics (satisfaction score)
   - Device associations

6. **Relationship Mapping**:
   - `(UnifiDevice)-[:RESOURCE]->(UnifiSite)`
   - `(UnifiWlan)-[:RESOURCE]->(UnifiSite)`
   - `(UnifiPort)-[:HAS_PORT]->(UnifiDevice)`
   - `(UnifiClient)-[:RESOURCE]->(UnifiDevice)`

7. **Automatic Cleanup**: Removes stale nodes based on update tags

8. **Proper Resource Management**: Always closes connections via context management

## Usage

### Configuration

```bash
# Set your UniFi controller password
export UNIFI_PASSWORD="your-password"

# Run cartography with UniFi module
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --unifi-host "192.168.1.1" \
  --unifi-user "admin" \
  --unifi-password-env-var "UNIFI_PASSWORD" \
  --unifi-site "default" \
  --unifi-port 8443 \
  --selected-modules "create-indexes,unifi"
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--unifi-host` | Yes | - | UniFi controller hostname or IP |
| `--unifi-user` | Yes | - | Username for authentication |
| `--unifi-password-env-var` | Yes | - | Environment variable with password |
| `--unifi-site` | No | `default` | Site name to sync |
| `--unifi-port` | No | `8443` | Controller port |

## Test Coverage ✅

### Integration Tests (20+ tests)

**Site Tests:**
- ✅ Site loading verification
- ✅ Site property validation
- ✅ Stale site cleanup

**Device Tests:**
- ✅ Device loading verification
- ✅ Device property validation
- ✅ Device-to-site relationship mapping
- ✅ Stale device cleanup

**WLAN Tests:**
- ✅ WLAN loading verification
- ✅ WLAN property validation (security, guest mode)
- ✅ WLAN-to-site relationship mapping
- ✅ Stale WLAN cleanup

**Port Tests:**
- ✅ Port loading verification
- ✅ Port property validation (PoE, connectivity)
- ✅ Port-to-device relationship mapping
- ✅ Stale port cleanup

**Client Tests:**
- ✅ Client loading verification
- ✅ Client-to-device relationship mapping
- ✅ Client property validation (wireless vs wired)
- ✅ Disconnected client cleanup
- ✅ Guest vs. regular client distinction

### Unit Tests (3 tests)

**Utility Tests:**
- ✅ Controller creation with various parameters
- ✅ Custom site support
- ✅ Proper connection cleanup

All tests use `@pytest.mark.asyncio` and `AsyncMock` for proper async testing.

## Example Queries

After sync, query the graph:

```cypher
// Find all UniFi sites
MATCH (s:UnifiSite)
RETURN s.name, s.desc, s.role

// Find all devices in a site
MATCH (d:UnifiDevice)-[:RESOURCE]->(s:UnifiSite)
RETURN s.name as site, d.name as device, d.type, d.model
ORDER BY s.name, d.name

// Find all WLANs in a site
MATCH (w:UnifiWlan)-[:RESOURCE]->(s:UnifiSite)
RETURN s.name as site, w.name as wlan, w.security, w.is_guest
ORDER BY s.name, w.name

// Find all guest networks
MATCH (w:UnifiWlan {is_guest: true})
RETURN w.name, w.security, w.enabled

// Find switch ports with PoE enabled
MATCH (p:UnifiPort)-[:HAS_PORT]->(d:UnifiDevice)
WHERE p.poe_enable = true
RETURN d.name as switch, p.name as port, p.poe_mode, p.poe_voltage, p.up
ORDER BY d.name, p.port_idx

// Find all ports on a specific device
MATCH (p:UnifiPort)-[:HAS_PORT]->(d:UnifiDevice {name: 'Main Switch'})
RETURN p.name, p.port_idx, p.up, p.speed, p.poe_enable
ORDER BY p.port_idx

// Find all UniFi devices
MATCH (d:UnifiDevice)
RETURN d.name, d.model, d.type, d.adopted

// Find all clients and their connected devices
MATCH (c:UnifiClient)-[:RESOURCE]->(d:UnifiDevice)
RETURN c.ip, c.mac, c.oui, d.name, c.satisfaction
ORDER BY c.satisfaction DESC

// Find guest clients
MATCH (c:UnifiClient {is_guest: true})
RETURN c.ip, c.oui, c.satisfaction

// Find wireless clients with low satisfaction
MATCH (c:UnifiClient)-[:RESOURCE]->(d:UnifiDevice)
WHERE c.is_wired = false AND c.satisfaction < 90
RETURN c.ip, c.oui, c.satisfaction, d.name
ORDER BY c.satisfaction ASC

// Count clients per device
MATCH (c:UnifiClient)-[:RESOURCE]->(d:UnifiDevice)
RETURN d.name, d.model, count(c) as client_count
ORDER BY client_count DESC

// Find devices by type
MATCH (d:UnifiDevice)
WHERE d.type = 'uap'  // Access Points
RETURN d.name, d.model, d.adopted

// Network topology - Full hierarchy
MATCH path = (c:UnifiClient)-[:RESOURCE]->(d:UnifiDevice)-[:RESOURCE]->(s:UnifiSite)
RETURN path

// Find all active ports with clients potentially connected
MATCH (p:UnifiPort)-[:HAS_PORT]->(d:UnifiDevice)<-[:RESOURCE]-(c:UnifiClient)
WHERE p.up = true AND c.is_wired = true
RETURN d.name as switch, p.name as port, count(c) as client_count
ORDER BY client_count DESC

// Security audit: Find open guest networks
MATCH (w:UnifiWlan)
WHERE w.is_guest = true AND w.security = 'open'
RETURN w.name, w.enabled, w.hide_ssid
```

## Security Considerations

1. **Password Storage**
   - ✅ Uses environment variables (not hardcoded)
   - ✅ Never logged or stored in Neo4j
   - ✅ Follows Cartography password handling patterns

2. **SSL/TLS**
   - ✅ Uses SSL by default
   - ✅ Handles self-signed certificates (common for UniFi)
   - ⚠️ Certificate verification disabled (standard for local controllers)
   - 🔒 For production, consider proper certificate management

3. **API Access**
   - Controller credentials should have read-only access
   - Consider creating dedicated service account
   - Rotate credentials regularly

4. **Network Security**
   - Use HTTPS for controller connections
   - Consider VPN/bastion host for remote controllers
   - Firewall UniFi controller appropriately

## Future Enhancements

### Additional Data
- ✅ Port configurations on switches (implemented)
- ✅ WLAN/network configurations (implemented)
- ✅ Site information and hierarchies (implemented)
- DPI (Deep Packet Inspection) stats
- Historical connection data
- Firewall rules
- VLANs and network segments
- RADIUS server configurations

### Advanced Features
- Track roaming events
- Client session history
- Network topology mapping
- Anomaly detection (unusual clients)
- Bandwidth utilization tracking
- Uptime monitoring

### Performance
- Batch processing for large deployments
- Incremental updates (only changed data)
- Parallel site syncing
- Websocket support for real-time updates

## Testing

### Prerequisites
```bash
# Install dependencies
pip install -e '.[dev]'

# Start Neo4j (Docker)
docker run -d \
  --name neo4j-test \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/test \
  neo4j:5
```

### Run Tests
```bash
# Run all UniFi tests
pytest tests/integration/cartography/intel/unifi/ -v
pytest tests/unit/cartography/intel/unifi/ -v

# Run with coverage
pytest tests/integration/cartography/intel/unifi/ \
  --cov=cartography.intel.unifi \
  --cov-report=html

# Run specific test
pytest tests/integration/cartography/intel/unifi/test_devices.py::test_load_unifi_devices -v
```

## Troubleshooting

### Common Issues

**Connection Errors:**
```
Failed to connect to UniFi controller
```
- Verify host and port are correct
- Check firewall rules
- Ensure controller is accessible from Cartography host

**Authentication Failures:**
```
LoginRequired exception
```
- Verify username and password are correct
- Check that account has proper permissions
- Ensure password environment variable is set correctly

**SSL Certificate Errors:**
```
SSL verification failed
```
- Current implementation disables SSL verification (common for self-signed certs)
- If you need strict SSL, modify `util.py` to use proper certificate validation

**Async Runtime Warnings:**
```
RuntimeWarning: coroutine was never awaited
```
- This usually indicates a test wasn't marked with `@pytest.mark.asyncio`
- Or an async function was called without `await`

## Migration Notes

### Changes from unificontrol

1. **API Changes:**
   - `UnifiClient` → `Controller`
   - Synchronous → Asynchronous
   - Direct method calls → `await controller.devices.update()`

2. **Data Access:**
   - Old: `client.list_devices_basic()`
   - New: `await controller.devices.update()` then iterate `controller.devices.values()`

3. **Connection Management:**
   - Old: Simple instantiation
   - New: Create session, config, controller, then login

4. **Resource Cleanup:**
   - Old: Automatic
   - New: Manual session cleanup with `await session.close()`

## Production Readiness ✅

The current implementation is **production-ready** with:

- ✅ **Active library** (aiounifi v81+)
- ✅ **Comprehensive test coverage**
- ✅ **Proper async patterns**
- ✅ **Resource cleanup**
- ✅ **Error handling**
- ✅ **Follows Cartography conventions**

## Performance Characteristics

- **Async I/O** - Non-blocking network operations
- **Connection pooling** - Via aiohttp session
- **Timeout handling** - 60-second timeout for operations
- **Memory efficient** - Streams data instead of loading everything at once

## References

- [aiounifi GitHub](https://github.com/Kane610/aiounifi) - Official repository
- [aiounifi PyPI](https://pypi.org/project/aiounifi/) - Package page
- [Home Assistant UniFi Integration](https://www.home-assistant.io/integrations/unifi/) - Production usage example
- [UniFi Controller API (unofficial)](https://ubntwiki.com/products/software/unifi-controller/api) - API documentation
- [UniFi Network Application](https://www.ui.com/software/) - Official UniFi software

## Changelog

### v2.1 - Expanded Object Support (Current)
- ✅ Added UniFi Site tracking and site hierarchy
- ✅ Added WLAN (wireless network) configuration tracking
- ✅ Added switch Port tracking with PoE and connectivity details
- ✅ Implemented hierarchical data model:
  - Sites contain Devices and WLANs
  - Devices have Ports
  - Clients connect to Devices
- ✅ Added comprehensive test coverage for new objects (20+ tests)
- ✅ Updated documentation with new queries and examples
- ✅ Hierarchical sync order for data integrity

### v2.0 - aiounifi Migration
- ✅ Migrated from unificontrol to aiounifi
- ✅ Implemented async/await patterns
- ✅ Added proper connection management
- ✅ Updated all tests for async
- ✅ Added port configuration option
- ✅ Improved error handling
- ✅ Better SSL/TLS handling

### v1.0 - Initial Implementation
- ✅ Basic device and client tracking
- ✅ Data models and relationships
- ✅ Integration with Cartography pipeline
- ✅ Test coverage
