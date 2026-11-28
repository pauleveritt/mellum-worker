from mdtable import render


def test_numbers_right_text_left_with_padding():
    out = render([{"name": "ab", "n": 5}, {"name": "abcdef", "n": 1234}])
    assert out == (
        "| name   |    n |\n"
        "| :----- | ---: |\n"
        "| ab     |    5 |\n"
        "| abcdef | 1234 |\n"
    )


def test_columns_from_every_row_and_missing_cells_empty():
    out = render([{"a": "x"}, {"b": "yy", "a": "z"}])
    assert out == (
        "| a   | b   |\n"
        "| :-- | :-- |\n"
        "| x   |     |\n"
        "| z   | yy  |\n"
    )


def test_explicit_center_alignment_and_pipe_escape():
    out = render([{"k": "a|b", "pos": "x"}], align={"pos": "center"})
    assert out == (
        "| k    | pos |\n"
        "| :--- | :-: |\n"
        "| a\\|b |  x  |\n"
    )
