import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import requests

from cartography.intel.fleetdm.utils import _find_resource_key
from cartography.intel.fleetdm.utils import is_license_error
from cartography.intel.fleetdm.utils import log_optional_fetch_failure
from cartography.intel.fleetdm.utils import paginated_get


def _mock_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_find_resource_key_matches_known_key():
    assert _find_resource_key({"hosts": [{"id": 1}]}) == "hosts"
    assert _find_resource_key({"software_titles": []}) == "software_titles"


def test_find_resource_key_no_match():
    assert _find_resource_key({"unrelated_key": [1, 2, 3]}) is None
    assert _find_resource_key({}) is None


def test_paginated_get_top_level_list_single_page():
    session = MagicMock()
    session.get.return_value = _mock_response([{"id": 1}, {"id": 2}])

    result = list(paginated_get(session, "http://fleet/api/hosts", page_size=100))

    assert result == [{"id": 1}, {"id": 2}]
    assert session.get.call_count == 1


def test_paginated_get_top_level_list_multiple_pages():
    session = MagicMock()
    page_1 = [{"id": i} for i in range(3)]
    page_2 = [{"id": 3}]
    session.get.side_effect = [_mock_response(page_1), _mock_response(page_2)]

    result = list(paginated_get(session, "http://fleet/api/hosts", page_size=3))

    assert result == page_1 + page_2
    assert session.get.call_count == 2


def test_paginated_get_dict_with_resource_key_and_meta():
    session = MagicMock()
    payload = {
        "users": [{"id": 1}],
        "meta": {"has_next_results": False},
    }
    session.get.return_value = _mock_response(payload)

    result = list(paginated_get(session, "http://fleet/api/users", page_size=100))

    assert result == [{"id": 1}]
    assert session.get.call_count == 1


def test_paginated_get_dict_with_no_resource_list_stops():
    session = MagicMock()
    session.get.return_value = _mock_response({"unrelated": "value"})

    result = list(paginated_get(session, "http://fleet/api/unknown"))

    assert result == []
    assert session.get.call_count == 1


@patch("cartography.intel.fleetdm.utils._TIMEOUT", (60, 60))
def test_paginated_get_uses_page_and_per_page_params():
    session = MagicMock()
    session.get.return_value = _mock_response([])

    list(paginated_get(session, "http://fleet/api/hosts", page_size=50))

    _, kwargs = session.get.call_args
    assert kwargs["params"]["page"] == 0
    assert kwargs["params"]["per_page"] == 50


def _http_error(status_code):
    response = MagicMock()
    response.status_code = status_code
    return requests.HTTPError("boom", response=response)


def test_is_license_error_classifies_by_status():
    assert is_license_error(_http_error(402)) is True
    assert is_license_error(_http_error(403)) is True
    assert is_license_error(_http_error(404)) is False
    assert is_license_error(_http_error(500)) is False
    assert is_license_error(requests.ConnectionError("no response")) is False


def test_log_optional_fetch_failure_warns_on_refusal(caplog):
    with caplog.at_level(logging.DEBUG, logger="cartography.intel.fleetdm.utils"):
        log_optional_fetch_failure(_http_error(402), "FleetDM fleets")

    assert caplog.records[-1].levelno == logging.WARNING
    assert "ABSENT" in caplog.records[-1].getMessage()


def test_log_optional_fetch_failure_debugs_on_absent_feature(caplog):
    with caplog.at_level(logging.DEBUG, logger="cartography.intel.fleetdm.utils"):
        log_optional_fetch_failure(_http_error(404), "FleetDM fleets", fleet_id=1)

    assert caplog.records[-1].levelno == logging.DEBUG
    assert "fleet_id=1" in caplog.records[-1].getMessage()


def test_log_optional_fetch_failure_warns_on_unexpected_error(caplog):
    with caplog.at_level(logging.DEBUG, logger="cartography.intel.fleetdm.utils"):
        log_optional_fetch_failure(_http_error(500), "FleetDM fleets")

    assert caplog.records[-1].levelno == logging.WARNING
