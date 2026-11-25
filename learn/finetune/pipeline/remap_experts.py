"""Slice mlx-lm's stacked experts (mlp.switch_mlp.{proj}.weight [E,out,in]) into the per-expert
tensors llama.cpp's Mellum converter wants (mlp.experts.{x}.{proj}.weight). Pure slice, in place."""
import json, re, sys, pathlib
from safetensors.torch import load_file, save_file
d = pathlib.Path(sys.argv[1]); idx_p = d / "model.safetensors.index.json"
idx = json.loads(idx_p.read_text()); wm = {}; n = 0
for shard in sorted({v for v in idx["weight_map"].values()}):
    t = load_file(d / shard); out = {}
    for k, v in t.items():
        m = re.match(r"(model\.layers\.\d+\.mlp)\.switch_mlp\.(\w+)\.weight$", k)
        if m:
            for x in range(v.shape[0]):
                nk = f"{m.group(1)}.experts.{x}.{m.group(2)}.weight"; out[nk] = v[x].contiguous(); wm[nk] = shard
            n += 1
        else:
            out[k] = v; wm[k] = shard
    save_file(out, d / shard, metadata={"format": "pt"}); del t, out
idx["weight_map"] = wm; idx_p.write_text(json.dumps(idx, indent=2))
print(f"remapped {n} stacked expert tensors")
