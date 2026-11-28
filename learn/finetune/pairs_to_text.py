#!/usr/bin/env python3
"""Decode a pair set to text, for trainers that don't use Mellum's token ids (an SFT setup, another tokenizer).

    uv run --no-project --with transformers --with tokenizers --with jinja2 \
      python pairs_to_text.py data_dpo_mix_tools mix_tools.text.jsonl [tokenizer]

`tokenizer` defaults to JetBrains/Mellum2.1-12B-A2.5B-Thinking (a local model folder works too). One JSONL row per
pair, in the set's order:

- `kind`: the pair type (`medium:p3` a whole phase, `...:step`, `...:shell`, `...:outside`, `...:unused`,
  `...:idiom`), and `src`, the runs it came from;
- `text`: the chosen side as one ChatML string, exactly as the model saw it;
- `segments`: the chosen side as consecutive `{"train", "text"}` spans, `train` true on the tokens DPO scored (the
  model's own turns; for step, shell and other one-call pairs, only the tool call);
- `rejected_segments`: the rejected side, the same way.

For SFT, train on `segments` with loss on the `train` spans only, or on `text` with assistant-only loss. The
rejected side is there for preference trainers.
"""
import json
import sys

from pairs_io import read_pairs

MELLUM = "JetBrains/Mellum2.1-12B-A2.5B-Thinking"


def segments(ids, mask, decode):
    """Consecutive spans of `ids` with the same mask value, decoded."""
    out, start = [], 0
    for i in range(1, len(ids) + 1):
        if i == len(ids) or mask[i] != mask[start]:
            out.append({"train": bool(mask[start]), "text": decode(ids[start:i])})
            start = i
    return out


def main():
    from transformers import AutoTokenizer
    data, out = sys.argv[1], sys.argv[2]
    tok = AutoTokenizer.from_pretrained(sys.argv[3] if len(sys.argv) > 3 else MELLUM)
    n = 0
    with open(out, "w") as f:
        for r in read_pairs(data, "train"):
            f.write(json.dumps({"kind": r["phase"], "src": r["src"], "text": tok.decode(r["chosen"]),
                                "segments": segments(r["chosen"], r["chosen_mask"], tok.decode),
                                "rejected_segments": segments(r["rejected"], r["rejected_mask"], tok.decode)},
                               ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} pairs -> {out}")


if __name__ == "__main__":
    main()
