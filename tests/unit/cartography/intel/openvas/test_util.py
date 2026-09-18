import logging

from gvm.errors import GvmError
from gvm.errors import GvmResponseError

from cartography.intel.openvas.util import is_permission_error
from cartography.intel.openvas.util import log_optional_fetch_failure


def test_is_permission_error_recognizes_gmp_status_strings():
    # python-gvm carries the GMP status as a string, not an int.
    assert is_permission_error(GvmResponseError(status="403", message="forbidden"))
    assert is_permission_error(GvmResponseError(status="401", message="auth first"))
    assert not is_permission_error(GvmResponseError(status="404", message="missing"))
    assert not is_permission_error(GvmError("connection reset"))


def test_permission_denial_logs_at_warning(caplog):
    caplog.set_level(logging.DEBUG, logger="cartography.intel.openvas.util")

    log_optional_fetch_failure(
        GvmResponseError(status="403", message="forbidden"),
        "OpenVAS get_credentials",
    )

    record = caplog.records[-1]
    assert record.levelno == logging.WARNING
    assert "ABSENT from the graph" in record.getMessage()


def test_unknown_command_logs_at_debug(caplog):
    caplog.set_level(logging.DEBUG, logger="cartography.intel.openvas.util")

    log_optional_fetch_failure(
        GvmResponseError(status="404", message="unknown command"),
        "OpenVAS get_tls_certificates",
    )

    assert caplog.records[-1].levelno == logging.DEBUG


def test_other_failures_log_at_warning(caplog):
    caplog.set_level(logging.DEBUG, logger="cartography.intel.openvas.util")

    log_optional_fetch_failure(GvmError("connection reset"), "OpenVAS get_results")

    assert caplog.records[-1].levelno == logging.WARNING
