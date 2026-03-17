## UniFi Configuration

Follow these steps to analyze UniFi network objects with Cartography.

1. Prepare your UniFi controller credentials.
    1. Ensure you have a UniFi Network Application or UniFi OS console running (self-hosted or cloud).
    1. Create or use an existing local admin account with read access to the site you want to sync.
    1. Populate environment variables with your credentials, e.g.:
        ```bash
        export UNIFI_USER=admin
        export UNIFI_PASSWORD=your_password
        ```

1. Run Cartography with the required parameters:

    ```bash
    cartography \
      --unifi-host <controller-ip-or-hostname> \
      --unifi-user-env-var UNIFI_USER \
      --unifi-password-env-var UNIFI_PASSWORD \
      --unifi-site default
    ```

    Alternatively, you can pass the username directly via `--unifi-user`:

    ```bash
    cartography \
      --unifi-host <controller-ip-or-hostname> \
      --unifi-user admin \
      --unifi-password-env-var UNIFI_PASSWORD \
      --unifi-site default
    ```

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `--unifi-host` | IP address or hostname of the UniFi controller |
| `--unifi-user` or `--unifi-user-env-var` | Username (or env var name) for authentication |
| `--unifi-password-env-var` | Environment variable name containing the password |

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--unifi-site` | `default` | UniFi site name to sync |
| `--unifi-port` | `443` | Controller HTTPS port |
| `--unifi-verify-ssl` | `False` | Verify SSL certificate (disable for self-signed certs) |

### Notes

- The default port is `443`, which is used by UniFi OS devices (UDM, UDM-Pro, UDM-SE) and cloud controllers. For legacy self-hosted UniFi Network Applications, use `--unifi-port 8443`.
- Many self-hosted UniFi controllers use self-signed TLS certificates. Set `--unifi-verify-ssl False` (the default) to allow connections to such controllers.
- The module requires `aiounifi>=81` and Python 3.12+.
