"""Tests for the grounded docs lookup (BM25 over venv packages)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import docs_lookup  # noqa: E402


def test_tokenize_splits_camel_and_snake_case():
    toks = docs_lookup.tokenize("RedirectResponse status_code")
    assert "redirectresponse" in toks  # the whole identifier
    assert "redirect" in toks and "response" in toks  # camelCase split
    assert "status" in toks and "code" in toks  # snake_case split


def test_bm25_ranks_the_relevant_doc_first():
    corpus = [
        docs_lookup.tokenize("class RedirectResponse status_code int = 307 location header"),
        docs_lookup.tokenize("class JSONResponse media_type application json render content"),
        docs_lookup.tokenize("def connect database sqlite cursor execute"),
    ]
    bm = docs_lookup.BM25(corpus)
    top = bm.top(docs_lookup.tokenize("RedirectResponse status code default"), k=1)
    assert top and top[0][0] == 0  # the RedirectResponse doc wins


def test_extract_chunks_captures_signature_with_default_value(tmp_path):
    mod = tmp_path / "responses.py"
    mod.write_text(
        "class RedirectResponse(Response):\n"
        "    def __init__(self, url, status_code: int = 307):\n"
        "        '''Redirect to url.'''\n"
        "        self.status_code = status_code\n"
    )
    chunks = docs_lookup.extract_chunks(mod, tmp_path)
    ids = [c["id"] for c in chunks]
    assert any("RedirectResponse" in i for i in ids)
    cls = next(c for c in chunks if c["id"].endswith(":RedirectResponse"))
    assert "307" in cls["text"]  # the default value is in the chunk, so BM25 can surface it


def test_bm25_empty_corpus_is_safe():
    bm = docs_lookup.BM25([])
    assert bm.top(docs_lookup.tokenize("anything"), k=3) == []


def test_index_auto_rebuilds_when_a_package_is_installed(tmp_path):
    sp = tmp_path / "site-packages"
    sp.mkdir()
    (sp / "foo.py").write_text("def alpha():\n    pass\n")
    first = docs_lookup.load_index(sp)
    assert any("alpha" in c["id"] for c in first)
    assert not any("beta" in c["id"] for c in first)
    # the model installs a new package after the index was built
    (sp / "bar.py").write_text("def beta():\n    pass\n")
    assert docs_lookup.signature(sp) != docs_lookup.signature(tmp_path)  # sig tracks contents
    second = docs_lookup.load_index(sp)  # stale cache -> auto-rebuild
    assert any("beta" in c["id"] for c in second)  # the new package is now indexed
