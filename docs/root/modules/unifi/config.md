## UniFi Configuration

Follow these steps to analyze UniFi network objects with Cartography.

1. Prepare your UniFi controller credentials.
    1. Ensure you have a UniFi Network Application or UniFi OS console running (self-hosted or cloud).
    1. Create or use an existing local admin account with read access to the site you want to sync.
    1. Populate an environment variable with the password, e.g. `export UNIFI_PASSWORD=your_password`.

1. Run Cartography with the required parameters:

    ```bash
    cartography \
      --unifi-host <controller-ip-or-hostname> \
      --unifi-user <admin-username> \
      --unifi-password-env-var UNIFI_PASSWORD \
      --unifi-site default \
      --unifi-port 8443
    ```

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `--unifi-host` | IP address or hostname of the UniFi controller |
| `--unifi-user` | Username for authentication |
| `--unifi-password-env-var` | Environment variable name containing the password |

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--unifi-site` | `default` | UniFi site name to sync |
| `--unifi-port` | `8443` | Controller HTTPS port |
| `--unifi-verify-ssl` | `False` | Verify SSL certificate (disable for self-signed certs) |

### Notes

- Many self-hosted UniFi controllers use self-signed TLS certificates. Set `--unifi-verify-ssl False` (the default) to allow connections to such controllers.
- For UniFi OS devices (UDM, UDM-Pro, UDM-SE), the controller runs on port 443 by default. Use `--unifi-port 443` in that case.
- The module requires `aiounifi>=81` and Python 3.12+.
