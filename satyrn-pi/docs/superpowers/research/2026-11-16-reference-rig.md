# Reference rig: preserve the subject, identify the configuration

## What is measured / what is conjecture

**What is measured:** source configuration inspection at `0e4a9b68`, not a
Satyrn Pi server or model run. **What is conjecture:** that a rewritten package
on the selected configuration reproduces any historical performance.

## Evidence and decision

The source does not have one universal server build:

- [scripts/llama-release.sh:11](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/scripts/llama-release.sh#L11)
  defaults the installer to b12066.
- [scripts/baseline/pins.env:23](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/scripts/baseline/pins.env#L23)
  names a rented b11985 CUDA image.
- [install.sh:25](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/install.sh#L25)
  and its build check accept existing installations from build 9482 upward.
- [pyproject.toml:20](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/pyproject.toml#L20)
  supplies the local model and sampling settings; [scripts/backend.py:52](https://github.com/andrevanzuydam/mellum-worker/blob/0e4a9b6859cbe447adbca537c5738f24a862d214/scripts/backend.py#L52)
  constructs its serve flags.

**Documentation choice made while applying review:** use the source installer's
b12066 release for the new reference setup. This disambiguates the inherited-pin
requirement; it does not change Mellum 2.1 12B-A2.5B Thinking or its Q4_K_M quant.
Retain the source local settings: context 50000, max_tokens 16384, temperature
1.0, top_p 0.95 and top_k 20. These are configuration values copied from the
source, not newly measured optima. The API base is `http://127.0.0.1:8001/v1`.

Preserve the source serve flags as phase-4 input, recording any platform-specific
offload choice explicitly. No performance number transfers merely because the
model name and release tag match. Keep each imported record's original setup.

## Owner and work due

Phase 4, led by Andre/Paul with Ben reviewing the setup instructions, must
resolve the actual GGUF file and SHA-256, Hugging Face revision, llama.cpp source
commit, platform binary checksum or container digest, full serve flags and
request settings. A quant name or mutable image tag alone is insufficient
provenance. Capture those in the documented host card and prove the documented
setup answers a request before the phase closes.

Choose a supported reference platform in the phase-4 spec; mark unexercised
platforms accordingly. A rented batch must use the selected version, not inherit
b11985 merely because that old image exists. Provisioning stays outside eval.

## What would falsify this

If the cited revision does not contain these values, correct this inventory.
If b12066 cannot run the preserved model/settings on the chosen platform,
record the failure and an explicit configuration decision before declaring
setup complete; do not silently select another build.

## Risks

The source's GGUF selector is not a content pin. Native and CUDA artifacts
differ even at one server version. Historical baselines used several builds;
this document does not establish parity among them.
