import json, sys

CAP_MSG = 800      # max chars per message content (truncate big tool dumps)
CAP_TOTAL = 8000   # drop examples still larger than this (~2000 tokens)

def compact_msg(m):
    c = m.get("content")
    if isinstance(c, str) and len(c) > CAP_MSG:
        m = dict(m); m["content"] = c[:CAP_MSG] + " …[truncated]"
    return m

def total_chars(r):
    return sum(len(json.dumps(m)) for m in r["messages"]) + len(json.dumps(r.get("tools") or []))

for name in ("train", "valid"):
    path = f"data_adherence/{name}.jsonl"
    rows = [json.loads(l) for l in open(path)]
    out = []
    for r in rows:
        r = dict(r); r["messages"] = [compact_msg(m) for m in r["messages"]]
        if total_chars(r) <= CAP_TOTAL:
            out.append(r)
    with open(path, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    lens = sorted(total_chars(r) for r in out)
    p = lambda q: lens[min(int(len(lens) * q), len(lens) - 1)] if lens else 0
    print(f"{name}: kept {len(out)}/{len(rows)}   chars p50={p(.5)} p90={p(.9)} max={lens[-1] if lens else 0}")
