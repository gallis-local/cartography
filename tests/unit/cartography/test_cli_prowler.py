import inspect
import unittest.mock
from typing import get_args

import cartography.cli


def test_cli_prowler_options_set_config(monkeypatch) -> None:
    # Arrange
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    monkeypatch.setenv("TEST_PROWLER_API_KEY", "api-key")
    monkeypatch.setenv("TEST_PROWLER_PASSWORD", "user-password")

    # Act
    with unittest.mock.patch(
        "cartography.sync.run_with_config",
        return_value=0,
    ) as run_with_config:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "prowler",
                "--prowler-api-url",
                "https://api.prowler.example",
                "--prowler-api-key-env-var",
                "TEST_PROWLER_API_KEY",
                "--prowler-email",
                "user@example.com",
                "--prowler-password-env-var",
                "TEST_PROWLER_PASSWORD",
                "--prowler-tenant-id",
                "d5b8b0b6-0000-4000-8000-000000000000",
            ],
        )

    # Assert
    assert exit_code == 0
    run_with_config.assert_called_once()
    config = run_with_config.call_args[0][1]
    assert config.prowler_api_url == "https://api.prowler.example"
    assert config.prowler_email == "user@example.com"
    assert config.prowler_tenant_id == "d5b8b0b6-0000-4000-8000-000000000000"


def test_cli_prowler_api_key_env_var_resolves_the_secret(monkeypatch) -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")
    monkeypatch.setenv("TEST_PROWLER_API_KEY", "api-key")

    # Act
    with unittest.mock.patch(
        "cartography.sync.run_with_config",
        return_value=0,
    ) as run_with_config:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "prowler",
                "--prowler-api-url",
                "https://api.prowler.example",
                "--prowler-api-key-env-var",
                "TEST_PROWLER_API_KEY",
            ],
        )

    # Assert: the config carries the secret, not the variable name.
    assert exit_code == 0
    config = run_with_config.call_args[0][1]
    assert config.prowler_api_key == "api-key"


def test_cli_prowler_password_env_var_resolves_the_secret(monkeypatch) -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")
    monkeypatch.setenv("TEST_PROWLER_PASSWORD", "user-password")

    # Act
    with unittest.mock.patch(
        "cartography.sync.run_with_config",
        return_value=0,
    ) as run_with_config:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "prowler",
                "--prowler-api-url",
                "https://api.prowler.example",
                "--prowler-email",
                "user@example.com",
                "--prowler-password-env-var",
                "TEST_PROWLER_PASSWORD",
            ],
        )

    # Assert: the config carries the secret, not the variable name.
    assert exit_code == 0
    config = run_with_config.call_args[0][1]
    assert config.prowler_password == "user-password"


def test_cli_prowler_api_key_uses_default_environment_variable(monkeypatch) -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")
    monkeypatch.setenv("PROWLER_API_KEY", "default-env-key")

    # Act
    with unittest.mock.patch(
        "cartography.sync.run_with_config",
        return_value=0,
    ) as run_with_config:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "prowler",
                "--prowler-api-url",
                "https://api.prowler.example",
            ],
        )

    # Assert
    assert exit_code == 0
    config = run_with_config.call_args[0][1]
    assert config.prowler_api_key == "default-env-key"


def test_cli_prowler_password_uses_default_environment_variable(monkeypatch) -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")
    monkeypatch.setenv("PROWLER_PASSWORD", "default-env-password")

    # Act
    with unittest.mock.patch(
        "cartography.sync.run_with_config",
        return_value=0,
    ) as run_with_config:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "prowler",
                "--prowler-api-url",
                "https://api.prowler.example",
                "--prowler-email",
                "user@example.com",
            ],
        )

    # Assert
    assert exit_code == 0
    config = run_with_config.call_args[0][1]
    assert config.prowler_password == "default-env-password"


def test_cli_prowler_env_var_defaults_are_declared() -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")

    # Act
    app = cli._build_app(
        cartography.cli._parse_selected_modules_from_argv(
            ["--selected-modules", "prowler", "--help"],
        ),
    )
    parameters = inspect.signature(app.registered_commands[0].callback).parameters

    # Assert
    assert parameters["prowler_api_key_env_var"].default == "PROWLER_API_KEY"
    assert parameters["prowler_password_env_var"].default == "PROWLER_PASSWORD"


def test_cli_does_not_accept_prowler_secrets_as_direct_options() -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")

    # Act
    app = cli._build_app(
        cartography.cli._parse_selected_modules_from_argv(
            ["--selected-modules", "prowler", "--help"],
        ),
    )
    annotations = app.registered_commands[0].callback.__annotations__

    # Assert: secrets are only readable from the environment.
    assert "prowler_api_key" not in annotations
    assert "prowler_password" not in annotations


def test_cli_selected_modules_prowler_shows_prowler_options() -> None:
    # Arrange
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "test")

    # Act
    app = cli._build_app(
        cartography.cli._parse_selected_modules_from_argv(
            ["--selected-modules", "prowler", "--help"],
        ),
    )
    annotations = app.registered_commands[0].callback.__annotations__

    # Assert
    assert get_args(annotations["prowler_api_url"])[1].hidden is False
    assert get_args(annotations["prowler_api_key_env_var"])[1].hidden is False
    assert get_args(annotations["prowler_email"])[1].hidden is False
    assert get_args(annotations["prowler_password_env_var"])[1].hidden is False
    assert get_args(annotations["prowler_tenant_id"])[1].hidden is False
