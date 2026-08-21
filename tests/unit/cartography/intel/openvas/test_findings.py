from xml.etree import ElementTree

import pytest

from cartography.intel.openvas.findings import _extract_cves
from cartography.intel.openvas.findings import _parse_tags
from cartography.intel.openvas.findings import _transform_nvt
from cartography.intel.openvas.findings import _transform_result
from cartography.intel.openvas.findings import transform_results
from tests.data.openvas.responses import GET_RESULTS_RESPONSE
from tests.data.openvas.responses import NVT_OID_1
from tests.data.openvas.responses import NVT_OID_2
from tests.data.openvas.responses import parse


def _results() -> list:
    response = parse(GET_RESULTS_RESPONSE)
    return response.findall("result")


def test_parse_tags():
    assert _parse_tags("cvss_base_vector=AV:N/AC:L;summary=some text") == {
        "cvss_base_vector": "AV:N/AC:L",
        "summary": "some text",
    }


def test_parse_tags_empty():
    assert _parse_tags(None) == {}
    assert _parse_tags("") == {}


def test_extract_cves_dedupes_across_sources():
    nvt = ElementTree.fromstring(
        """
        <nvt id="1.3.6.1.4.1.25623.1.0.1">
            <cve>CVE-2024-1000, CVE-2024-2000</cve>
            <refs>
                <ref type="cve" id="CVE-2024-1000"/>
                <ref type="url" id="https://example.com"/>
            </refs>
            <tags>cve_id=CVE-2024-3000</tags>
        </nvt>
        """
    )
    assert _extract_cves(nvt) == ["CVE-2024-1000", "CVE-2024-2000", "CVE-2024-3000"]


def test_transform_result_first_result():
    result = _results()[0]
    transformed = _transform_result(result)

    assert transformed["host"] == "10.0.0.5"
    assert transformed["nvt_id"] == NVT_OID_1
    assert transformed["severity"] == 7.5
    assert transformed["has_cve"] == "true"
    assert transformed["cve_id"] == "CVE-2024-1000"
    assert transformed["cve_list"] == ["CVE-2024-1000"]
    assert transformed["task_name"] == "Full Scan"


def test_transform_result_no_cve():
    result = _results()[1]
    transformed = _transform_result(result)

    assert transformed["has_cve"] == "false"
    assert transformed["cve_id"] is None
    assert transformed["cve_list"] is None


def test_transform_result_missing_id_raises():
    result = ElementTree.fromstring("<result><name>no id</name></result>")
    with pytest.raises(ValueError):
        _transform_result(result)


def test_transform_nvt_captures_solution_type_and_method():
    result = _results()[0]
    nvt = result.find("nvt")
    transformed = _transform_nvt(nvt)

    assert transformed["id"] == NVT_OID_1
    assert transformed["solution_type"] == "VendorFix"
    assert transformed["cvss_base_vector"] == "AV:N/AC:L/Au:N/C:P/I:P/A:P"
    assert transformed["cve_list"] == ["CVE-2024-1000"]


def test_transform_nvt_missing_oid_raises():
    nvt = ElementTree.fromstring("<nvt><name>no oid</name></nvt>")
    with pytest.raises(ValueError):
        _transform_nvt(nvt)


def test_transform_results_dedupes_nvts_by_oid():
    result_data, nvt_data = transform_results(_results())

    assert len(result_data) == 2
    assert {nvt["id"] for nvt in nvt_data} == {NVT_OID_1, NVT_OID_2}
