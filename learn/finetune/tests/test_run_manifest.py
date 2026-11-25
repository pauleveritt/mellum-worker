"""run_manifest: everything needed to rebuild a trained model, pinned by checksum."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_manifest import build_manifest, parse_train_log  # noqa: E402

LOG = """train 120 pairs, valid 20 (held-out trajectories); 1 epochs x 30 updates
[eval] update 0: val loss 0.00250 acc 0.000 margin 0.00000
[train] ep 1 update 1/30: loss 0.00250 acc 0.000 margin 0.00000 | 6.4 min elapsed, ~186 min left, peak 41.0 GB
[eval] update 15: val loss 0.00240 acc 0.667 margin 0.01000
"""


def sha(b):
    return hashlib.sha256(b).hexdigest()


def test_parse_train_log_keeps_every_update_and_eval():
    log = parse_train_log(LOG)
    assert log["train"] == [{"update": 1, "loss": 0.0025, "acc": 0.0, "margin": 0.0}]
    assert [e["update"] for e in log["eval"]] == [0, 15]
    assert log["eval"][-1]["margin"] == 0.01


def test_manifest_pins_data_base_adapter_and_settings(tmp_path):
    data = tmp_path / "data"; data.mkdir()
    (data / "train.jsonl").write_bytes(b'{"a":1}\n{"a":2}\n'); (data / "valid.jsonl").write_bytes(b'{"a":3}\n')
    (data / "SOURCE.md").write_text("how it was built")
    base = tmp_path / "base"; base.mkdir()
    (base / "model.safetensors").write_bytes(b"weights"); (base / "config.json").write_text('{"quantization": {"bits": 6}}')
    adapter = tmp_path / "adapter"; adapter.mkdir()
    (adapter / "adapters.safetensors").write_bytes(b"lora"); (adapter / "adapter_config.json").write_text("{}")
    m = build_manifest(name="mix120", data_dir=data, base_dir=base, adapter_dir=adapter,
                       settings={"beta": 10, "lr": 2e-5}, train_log=LOG, repo=tmp_path)
    assert m["name"] == "mix120" and m["settings"] == {"beta": 10, "lr": 2e-5}
    assert m["data"]["files"]["train.jsonl"] == {"sha256": sha(b'{"a":1}\n{"a":2}\n'), "rows": 2}
    assert m["data"]["source_md"] is True
    assert m["base"]["files"]["model.safetensors"] == sha(b"weights")
    assert m["base"]["quantization"] == {"bits": 6}
    assert m["adapter"]["files"]["adapters.safetensors"] == sha(b"lora")
    assert m["log"]["eval"][-1]["update"] == 15
    assert "python" in m["packages"]
    json.dumps(m)  # serialisable
