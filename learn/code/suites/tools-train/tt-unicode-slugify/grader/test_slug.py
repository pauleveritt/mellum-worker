from filenames import safe_filename
from slug import slugify


def test_slugify_strips_accents_and_compat_forms():
    assert slugify("Crème Brûlée") == "creme-brulee"
    assert slugify("  Ångström -- ﬁle ①  ") == "angstrom-file-1"
    assert slugify("---") == ""


def test_safe_filename_uses_slugs_for_unicode():
    assert safe_filename("Crème Brûlée", "md") == "creme-brulee.md"
    assert safe_filename("Smörgåsbord 2024") == "smorgasbord-2024.txt"


def test_safe_filename_keeps_ascii_behaviour():
    assert safe_filename("Hello, World!") == "hello-world.txt"
    assert safe_filename("  Q3 report -- final ", "pdf") == "q3-report-final.pdf"
    assert safe_filename("???") == "untitled.txt"
    assert safe_filename("日本") == "untitled.txt"
