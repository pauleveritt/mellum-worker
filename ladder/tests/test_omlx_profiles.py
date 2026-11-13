import json

import pytest

from ladder.omlx_profiles import PROFILES, ProfileMismatch, apply_profile, profile


class Fake:
    def __init__(self, live, honest=True):
        self.live = dict(live)
        self.honest = honest
        self.puts = []

    def get_settings(self, model_id):
        return dict(self.live)

    def put_settings(self, model_id, patch):
        self.puts.append(patch)
        if self.honest:
            self.live.update(patch)
        return {"success": True}


def test_apply_verifies_live_settings():
    with pytest.raises(ProfileMismatch):
        apply_profile(Fake({"max_tokens": 4096}, honest=False), "m", "tuned")


def test_restore_runs_on_exception(tmp_path):
    path = tmp_path / "model_settings.json"
    path.write_text(json.dumps({"models": {"m": {"max_tokens": 4096}}}))
    fake = Fake({"max_tokens": 4096, "thinking_budget_enabled": False})
    with pytest.raises(RuntimeError), profile(fake, "m", "tuned", path):
        raise RuntimeError("pi timed out")
    assert fake.live["max_tokens"] == 4096
    assert fake.live["thinking_budget_enabled"] is False
    assert any(
        f.name.startswith("model_settings.json.bak-ladder-") for f in tmp_path.iterdir()
    )


def test_nopenalty_variant_differs_from_tuned_only_by_penalty():
    tuned, variant = PROFILES["tuned"], PROFILES["tuned-nopenalty"]
    assert variant["presence_penalty"] == 0.0
    assert {k: v for k, v in variant.items() if k != "presence_penalty"} == {
        k: v for k, v in tuned.items() if k != "presence_penalty"
    }


def test_profiles_have_required_keys():
    for name in ("baseline", "tuned", "tuned-nopenalty"):
        assert {
            "max_tokens",
            "thinking_budget_enabled",
            "presence_penalty",
        } <= PROFILES[name].keys()


def test_restore_is_verified_and_names_the_backup(tmp_path):
    from ladder.omlx_profiles import RestoreFailed

    path = tmp_path / "model_settings.json"
    path.write_text("{}")

    class StickyAfterApply(Fake):
        def put_settings(self, model_id, patch):
            self.puts.append(patch)
            if len(self.puts) == 1:
                self.live.update(patch)  # apply lands, restore is silently ignored
            return {"success": True}

    fake = StickyAfterApply(
        {"max_tokens": 4096, "thinking_budget_enabled": False, "presence_penalty": 0.0}
    )
    with pytest.raises(RestoreFailed) as info, profile(fake, "m", "tuned", path):
        pass
    assert ".bak-ladder-" in str(info.value)


def test_restore_failure_chains_the_original_error(tmp_path):
    from ladder.omlx_profiles import RestoreFailed

    class Dies(Fake):
        def put_settings(self, model_id, patch):
            if self.puts:
                raise ConnectionError("server down")
            self.puts.append(patch)
            self.live.update(patch)
            return {}

    dies = Dies(
        {"max_tokens": 4096, "thinking_budget_enabled": False, "presence_penalty": 0.0}
    )
    with (
        pytest.raises(RestoreFailed) as info,
        profile(dies, "m", "tuned", tmp_path / "s.json"),
    ):
        raise RuntimeError("pi timed out")
    chain, error = [], info.value
    while error is not None:
        chain.append(type(error))
        error = error.__cause__ or error.__context__
    assert RuntimeError in chain, chain


def test_request_params_exist_for_every_profile_and_are_not_server_keys():
    from ladder.omlx_profiles import REQUEST_PARAMS

    for name in PROFILES:
        assert name in REQUEST_PARAMS, name
        assert {"temperature", "max_tokens"} <= REQUEST_PARAMS[name].keys()
        for key in set(REQUEST_PARAMS[name]) & set(PROFILES[name]):
            assert REQUEST_PARAMS[name][key] == PROFILES[name][key], (
                f"{name}.{key}: request and server defaults disagree"
            )
    assert REQUEST_PARAMS["baseline"]["max_tokens"] == 4096
    assert REQUEST_PARAMS["tuned"]["presence_penalty"] == 0.5
    assert REQUEST_PARAMS["tuned-nopenalty"]["presence_penalty"] == 0


def test_check_effective_params_raises_on_a_forwarded_key_mismatch():
    from ladder.omlx_profiles import REQUEST_PARAMS, check_effective_params

    sent = dict(REQUEST_PARAMS["tuned"])
    check_effective_params(sent, "tuned")
    sent["presence_penalty"] = 0
    with pytest.raises(ProfileMismatch):
        check_effective_params(sent, "tuned")


def test_effective_request_applies_sampling_overrides_and_rejects_others():
    from ladder.omlx_profiles import REQUEST_PARAMS, effective_request

    assert effective_request("tuned") == REQUEST_PARAMS["tuned"]
    merged = effective_request("tuned", {"temperature": 0.7, "top_p": 0.9})
    assert merged["temperature"] == 0.7 and merged["top_p"] == 0.9
    # everything else is still the profile's
    assert merged["presence_penalty"] == REQUEST_PARAMS["tuned"]["presence_penalty"]
    # a non-sampling key is not silently accepted as an override
    with pytest.raises(KeyError):
        effective_request("tuned", {"presence_penalty": 0.1})


def test_check_effective_params_honours_overrides():
    from ladder.omlx_profiles import REQUEST_PARAMS, check_effective_params

    sent = {**REQUEST_PARAMS["tuned"], "temperature": 0.7}
    # without the override the greedy temperature is expected, so this mismatches
    with pytest.raises(ProfileMismatch):
        check_effective_params(sent, "tuned")
    # with the override declared, the sent request is correct
    check_effective_params(sent, "tuned", {"temperature": 0.7})


def test_max_tokens_is_an_overridable_request_param():
    # the effort ramp sets a small max_tokens for quick early slices, so it must
    # be overridable per re-dispatch (it flows to the agent entry's maxTokens).
    from ladder.omlx_profiles import OVERRIDABLE_REQUEST_PARAMS, effective_request

    assert "max_tokens" in OVERRIDABLE_REQUEST_PARAMS
    assert effective_request("tuned", {"max_tokens": 2048})["max_tokens"] == 2048


def test_seed_is_an_overridable_request_param():
    # re-dispatch varies the seed per retry, so seed must be overridable (not a
    # server-only key). It does nothing at temperature 0, but the retry ramp
    # raises temperature, where a distinct seed makes each retry reproducible.
    from ladder.omlx_profiles import OVERRIDABLE_REQUEST_PARAMS, effective_request

    assert "seed" in OVERRIDABLE_REQUEST_PARAMS
    assert effective_request("tuned", {"seed": 43})["seed"] == 43
