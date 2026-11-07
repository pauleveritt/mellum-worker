import pytest

from ladder.request_profiles import (
    OVERRIDABLE_REQUEST_PARAMS,
    REQUEST_PARAMS,
    ProfileMismatch,
    check_effective_params,
    effective_request,
)


def test_nopenalty_variant_differs_from_tuned_only_by_penalty():
    tuned, variant = REQUEST_PARAMS["tuned"], REQUEST_PARAMS["tuned-nopenalty"]
    assert variant["presence_penalty"] == 0
    assert {k: v for k, v in variant.items() if k != "presence_penalty"} == {
        k: v for k, v in tuned.items() if k != "presence_penalty"
    }


def test_request_params_exist_for_every_profile_with_the_required_keys():
    for name in ("baseline", "tuned", "tuned-nopenalty"):
        assert {"temperature", "max_tokens", "presence_penalty"} <= REQUEST_PARAMS[
            name
        ].keys()
    assert REQUEST_PARAMS["baseline"]["max_tokens"] == 4096
    assert REQUEST_PARAMS["tuned"]["presence_penalty"] == 0.5
    assert REQUEST_PARAMS["tuned-nopenalty"]["presence_penalty"] == 0


def test_check_effective_params_raises_on_a_forwarded_key_mismatch():
    sent = dict(REQUEST_PARAMS["tuned"])
    check_effective_params(sent, "tuned")
    sent["presence_penalty"] = 0
    with pytest.raises(ProfileMismatch):
        check_effective_params(sent, "tuned")


def test_effective_request_applies_sampling_overrides_and_rejects_others():
    assert effective_request("tuned") == REQUEST_PARAMS["tuned"]
    merged = effective_request("tuned", {"temperature": 0.7, "top_p": 0.9})
    assert merged["temperature"] == 0.7 and merged["top_p"] == 0.9
    # everything else is still the profile's
    assert merged["presence_penalty"] == REQUEST_PARAMS["tuned"]["presence_penalty"]
    # a non-sampling key is not silently accepted as an override
    with pytest.raises(KeyError):
        effective_request("tuned", {"presence_penalty": 0.1})


def test_check_effective_params_honours_overrides():
    sent = {**REQUEST_PARAMS["tuned"], "temperature": 0.7}
    # without the override the greedy temperature is expected, so this mismatches
    with pytest.raises(ProfileMismatch):
        check_effective_params(sent, "tuned")
    # with the override declared, the sent request is correct
    check_effective_params(sent, "tuned", {"temperature": 0.7})


def test_max_tokens_is_an_overridable_request_param():
    # the effort ramp sets a small max_tokens for quick early slices, so it must
    # be overridable per re-dispatch (it flows to the agent entry's maxTokens).
    assert "max_tokens" in OVERRIDABLE_REQUEST_PARAMS
    assert effective_request("tuned", {"max_tokens": 2048})["max_tokens"] == 2048


def test_seed_is_an_overridable_request_param():
    # re-dispatch varies the seed per retry, so seed must be overridable (not a
    # server-only key). It does nothing at temperature 0, but the retry ramp
    # raises temperature, where a distinct seed makes each retry reproducible.
    assert "seed" in OVERRIDABLE_REQUEST_PARAMS
    assert effective_request("tuned", {"seed": 43})["seed"] == 43
