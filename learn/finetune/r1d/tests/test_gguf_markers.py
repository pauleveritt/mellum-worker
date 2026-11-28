"""The converter marks any `<｜...｜>` token as CONTROL, which llama-server drops from the text its tool-call parser
reads. gguf_markers.py sets the tool markers to USER_DEFINED in place and touches nothing else."""
import os
import sys
from pathlib import Path

import numpy as np

LC = Path.home() / ".cache/mellum-llamacpp-cd959bae9/gguf-py"
sys.path.insert(0, str(LC)); sys.path.insert(0, str(Path(__file__).parent.parent))
import gguf  # noqa: E402
from gguf_markers import plain_markers  # noqa: E402


def tiny(path, tokens, types):
    w = gguf.GGUFWriter(str(path), "qwen2")
    w.add_token_list(tokens); w.add_token_types(types)
    w.add_tensor("t", np.zeros((2, 2), dtype=np.float32))
    w.write_header_to_file(); w.write_kv_data_to_file(); w.write_tensors_to_file(); w.close()


def types_of(path):
    f = gguf.GGUFReader(str(path)).fields["tokenizer.ggml.token_type"]
    return [int(f.parts[i][0]) for i in f.data]


def test_only_the_named_markers_become_user_defined(tmp_path):
    p = tmp_path / "m.gguf"
    C, U, N = gguf.TokenType.CONTROL, gguf.TokenType.USER_DEFINED, gguf.TokenType.NORMAL
    tiny(p, ["a", "<｜end▁of▁sentence｜>", "<｜tool▁sep｜>", "<｜think▁on｜>"], [N, C, C, C])
    changed = plain_markers(p, ["<｜tool▁sep｜>"])
    assert changed == {"<｜tool▁sep｜>": 2}
    assert types_of(p) == [N, C, U, C]


def test_a_missing_marker_is_an_error(tmp_path):
    p = tmp_path / "m.gguf"
    tiny(p, ["a"], [gguf.TokenType.NORMAL])
    try:
        plain_markers(p, ["<｜tool▁sep｜>"])
    except KeyError:
        return
    raise AssertionError("missing marker ignored")
