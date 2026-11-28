from filenames import safe_filename


def test_ascii_titles():
    assert safe_filename("Hello, World!") == "hello-world.txt"
    assert safe_filename("  Q3 report -- final ", "pdf") == "q3-report-final.pdf"


def test_empty_title_falls_back():
    assert safe_filename("???") == "untitled.txt"
