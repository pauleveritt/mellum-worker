from stock.parsers import parse_record


def test_parses_a_valid_line():
    record = parse_record("AB-1; 4; CPT")
    assert (record.sku, record.qty, record.warehouse) == ("AB-1", 4, "CPT")
