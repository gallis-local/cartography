"""
Shared fixtures and helpers for the OpenVAS integration tests.

A FakeGmp stands in for the GMP protocol session (the external boundary);
responses are realistic gvmd XML parsed into ElementTree.
"""

from contextlib import contextmanager

from cartography.client.core.tx import load
from cartography.models.openvas.instance import OpenVASInstanceSchema
from tests.data.openvas.responses import GET_CONFIGS_RESPONSE
from tests.data.openvas.responses import GET_CREDENTIALS_RESPONSE
from tests.data.openvas.responses import GET_HOSTS_RESPONSE
from tests.data.openvas.responses import GET_PORT_LISTS_RESPONSE
from tests.data.openvas.responses import GET_RESULTS_RESPONSE
from tests.data.openvas.responses import GET_SCHEDULES_RESPONSE
from tests.data.openvas.responses import GET_TARGETS_RESPONSE
from tests.data.openvas.responses import GET_TASKS_RESPONSE
from tests.data.openvas.responses import GET_TLS_CERTIFICATES_RESPONSE
from tests.data.openvas.responses import INSTANCE_ID
from tests.data.openvas.responses import parse

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 123456790


class FakeGmp:
    """In-memory GMP session serving the fixture responses."""

    def __init__(self) -> None:
        self._responses = {
            "get_hosts": GET_HOSTS_RESPONSE,
            "get_tasks": GET_TASKS_RESPONSE,
            "get_results": GET_RESULTS_RESPONSE,
            "get_tls_certificates": GET_TLS_CERTIFICATES_RESPONSE,
            "get_targets": GET_TARGETS_RESPONSE,
            "get_configs": GET_CONFIGS_RESPONSE,
            "get_schedules": GET_SCHEDULES_RESPONSE,
            "get_port_lists": GET_PORT_LISTS_RESPONSE,
            "get_credentials": GET_CREDENTIALS_RESPONSE,
        }
        self.calls: dict[str, list[dict]] = {name: [] for name in self._responses}

    def __getattr__(self, name: str):
        if name in self._responses:

            def _handler(**kwargs):
                self.calls[name].append(kwargs)
                return parse(self._responses[name])

            return _handler
        raise AttributeError(name)

    def authenticate(self, username: str, password: str) -> None:  # noqa: ARG002
        pass

    def close(self) -> None:
        pass

    def __enter__(self) -> "FakeGmp":
        return self

    def __exit__(self, *args) -> None:
        self.close()


@contextmanager
def gmp_session_fixture():
    yield FakeGmp()


def seed_instance(neo4j_session) -> None:
    """Load the OpenVASInstance tenant node via the Cartography loader."""
    load(
        neo4j_session,
        OpenVASInstanceSchema(),
        [{"id": INSTANCE_ID}],
        lastupdated=TEST_UPDATE_TAG,
    )


def common_job_parameters() -> dict:
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OPENVAS_INSTANCE_ID": INSTANCE_ID,
    }
