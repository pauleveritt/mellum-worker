"""serve_argv draft-MTP wiring (MELLUM_DRAFT), shown to fail first.

Mellum's MTP is self-speculative: the MTP-bundled gguf is served AS the main
model with --spec-type draft-mtp (no sidecar -md model). Needs llama.cpp
>= b11747.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("backend", Path(__file__).parent / "backend.py")
backend = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(backend)

SETTINGS = {"model": "JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M", "context": 50000}
MTP = "/models/mtp-Mellum-MTP-Q4_K_M.gguf"


def test_no_draft_serves_base_via_hf(monkeypatch):
    monkeypatch.delenv("MELLUM_DRAFT", raising=False)
    argv = backend.serve_argv(SETTINGS)
    assert "-hf" in argv and SETTINGS["model"] in argv
    assert "--spec-type" not in argv
    assert "-md" not in argv


def test_draft_serves_mtp_model_with_draft_mtp(monkeypatch):
    monkeypatch.setenv("MELLUM_DRAFT", MTP)
    argv = backend.serve_argv(SETTINGS)
    # the MTP gguf is the MAIN model (-m), not a sidecar (-md), not -hf
    assert "-m" in argv and argv[argv.index("-m") + 1] == MTP
    assert "-hf" not in argv
    assert "-md" not in argv
    # self-speculation via the model's own nextn layers
    assert "--spec-type" in argv and argv[argv.index("--spec-type") + 1] == "draft-mtp"
    assert "--spec-draft-n-max" in argv


def test_draft_default_n_max_is_one(monkeypatch):
    monkeypatch.setenv("MELLUM_DRAFT", MTP)
    monkeypatch.delenv("MELLUM_DRAFT_NMAX", raising=False)
    argv = backend.serve_argv(SETTINGS)
    assert argv[argv.index("--spec-draft-n-max") + 1] == "1"
