import textkit
from textkit import normalize


def test_new_name_is_public_and_works():
    from textkit import normalize_text
    assert normalize_text("  Café   AU lait ") == "cafe au lait"
    assert "normalize_text" in textkit.__all__


def test_old_name_is_gone():
    assert not hasattr(normalize, "clean")
    assert not hasattr(textkit, "clean")
    assert "clean" not in textkit.__all__


def test_callers_still_work():
    from textkit.search import search
    from textkit.slug import slugify
    from textkit.tags import unique_tags
    assert slugify("Hello  Wörld") == "hello-world"
    assert search("ÉTÉ", ["un été chaud", "winter"]) == ["un été chaud"]
    assert unique_tags(["Python", " python ", "Rust"]) == ["python", "rust"]
