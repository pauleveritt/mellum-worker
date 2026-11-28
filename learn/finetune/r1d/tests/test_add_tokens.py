"""Adding DeepSeek's tool markers to the distill as real tokens, in its spare embedding rows."""
import json
import sys
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

sys.path.insert(0, str(Path(__file__).parent.parent))
from add_tokens import TOOL_TOKENS, add_to_tokenizer, init_rows  # noqa: E402

HF = Path.home() / "models/r1d-1.5b/hf"
SAMPLE = ("<｜Assistant｜>ok<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function<｜tool▁sep｜>read\n```json\n"
          '{"path": "a.py"}\n```<｜tool▁call▁end｜><｜tool▁calls▁end｜><｜end▁of▁sentence｜>')


def tokenizers():
    tok_json = json.loads((HF / "tokenizer.json").read_text())
    cfg = json.loads((HF / "tokenizer_config.json").read_text())
    new_json, new_cfg = add_to_tokenizer(tok_json, cfg, TOOL_TOKENS, start=151665)
    return Tokenizer.from_str(json.dumps(tok_json)), Tokenizer.from_str(json.dumps(new_json)), new_cfg


def test_the_markers_were_not_tokens_before():
    old, _, _ = tokenizers()
    assert all(len(old.encode(t, add_special_tokens=False).ids) > 1 for t in TOOL_TOKENS)


def test_each_marker_is_one_token_in_the_spare_rows():
    _, new, cfg = tokenizers()
    ids = [new.encode(t, add_special_tokens=False).ids for t in TOOL_TOKENS]
    assert ids == [[151665 + i] for i in range(len(TOOL_TOKENS))]
    assert max(i for [i] in ids) < 151936  # inside the existing embedding matrix: no resize
    assert {cfg["added_tokens_decoder"][str(151665 + i)]["content"] for i in range(len(TOOL_TOKENS))} == set(TOOL_TOKENS)


def test_a_tool_call_keeps_its_markers_whole_and_round_trips():
    _, new, _ = tokenizers()
    ids = new.encode(SAMPLE, add_special_tokens=False).ids
    assert sum(i >= 151665 for i in ids) == 5
    assert new.decode(ids, skip_special_tokens=False) == SAMPLE


def test_ordinary_text_tokenizes_exactly_as_before():
    old, new, _ = tokenizers()
    text = "def f(x):\n    return x + 1  # tool call, function, json ``` <think>ok</think>"
    assert old.encode(text).ids == new.encode(text).ids


def test_new_rows_start_at_the_mean_of_their_pieces_and_nothing_else_moves():
    rng = np.random.default_rng(0)
    w = rng.standard_normal((20, 4)).astype(np.float32)
    out = init_rows(w, {17: [1, 2, 3], 18: [5]})
    assert np.allclose(out[17], w[[1, 2, 3]].mean(0)) and np.allclose(out[18], w[5])
    keep = [i for i in range(20) if i not in (17, 18)]
    assert np.array_equal(out[keep], w[keep]) and out.shape == w.shape


def test_transformers_sees_the_same_ids_the_gguf_converter_will(tmp_path):
    """The converter reads the vocabulary through transformers: every old special token keeps its id."""
    from transformers import AutoTokenizer
    tok_json = json.loads((HF / "tokenizer.json").read_text())
    cfg = json.loads((HF / "tokenizer_config.json").read_text())
    new_json, new_cfg = add_to_tokenizer(tok_json, cfg, TOOL_TOKENS, start=151665)
    (tmp_path / "tokenizer.json").write_text(json.dumps(new_json))
    (tmp_path / "tokenizer_config.json").write_text(json.dumps(new_cfg))
    (tmp_path / "config.json").write_text((HF / "config.json").read_text())  # picks the Qwen2 tokenizer path
    old, new = AutoTokenizer.from_pretrained(HF), AutoTokenizer.from_pretrained(tmp_path)
    vocab = new.get_vocab()
    for t in tok_json["added_tokens"]:
        assert vocab[t["content"]] == t["id"], t["content"]
    assert [vocab[t] for t in TOOL_TOKENS] == list(range(151665, 151674))
    assert new.eos_token_id == old.eos_token_id and new.bos_token_id == old.bos_token_id
