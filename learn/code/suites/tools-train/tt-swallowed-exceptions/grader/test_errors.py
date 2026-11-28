import pytest

from stock.adjust import adjustment
from stock.importer import import_lines
from stock.parsers import RecordError, parse_record


def test_bad_lines_raise_record_error():
    assert issubclass(RecordError, ValueError)
    for bad in ("AB-1;four;CPT", "AB-1;3", ";2;CPT", "AB-1;-2;CPT"):
        with pytest.raises(RecordError):
            parse_record(bad)


def test_importer_skips_bad_lines_and_reports_line_numbers():
    result = import_lines(["A;1;CPT", "B;x;CPT", "", "C;2;JHB", "D;0;JHB"])
    assert [r.sku for r in result.records] == ["A", "C"]
    assert result.errors == [2, 5]


def test_single_adjustment_surfaces_the_error():
    with pytest.raises(RecordError):
        adjustment("ZZ;;CPT")
