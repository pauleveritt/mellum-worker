from textkit import clean, slugify


def test_clean_collapses_whitespace():
    assert clean("  Hello   World ") == "hello world"


def test_slugify():
    assert slugify("Crème Brûlée Recipes") == "creme-brulee-recipes"
