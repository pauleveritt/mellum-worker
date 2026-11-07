import json

from ladder.pi_profile import DEFAULT_BASE_URL, MODEL_ID, REPO_ROOT, direct_agent_dir


def test_ladder_direct_defaults_match_the_shipped_llama_reference(tmp_path):
    """The ladder's direct-mode defaults are the shipped llama reference template's
    values, so the measured path and what mellum-check reads cannot drift."""
    ref = json.loads(
        (REPO_ROOT / "templates" / "llama-model-settings.json").read_text()
    )
    assert MODEL_ID == ref["modelId"]
    assert DEFAULT_BASE_URL == ref["baseUrlDefault"]

    agent = direct_agent_dir(tmp_path / "agent", "baseline")
    models = json.loads((agent / "models.json").read_text())
    entry = models["providers"][ref["provider"]]["models"][0]
    assert entry["id"] == ref["modelId"]
    assert entry["contextWindow"] == ref["nCtxMin"]
    settings = json.loads((agent / "settings.json").read_text())
    assert settings["defaultProvider"] == ref["provider"]
