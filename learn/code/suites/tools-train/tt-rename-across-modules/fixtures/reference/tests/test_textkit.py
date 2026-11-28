from textkit import normalize_text, slugify


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  Hello   World ") == "hello world"


def test_slugify():
    assert slugify("Crème Brûlée Recipes") == "creme-brulee-recipes"
