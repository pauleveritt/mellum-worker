import json, sys

CAP = int(sys.argv[1]) if len(sys.argv) > 1 else 6000  # raw chars across all messages

def raw_chars(r):
    return sum(len(json.dumps(m)) for m in r["messages"]) + len(json.dumps(r.get("tools") or []))

for name in ("train", "valid"):
    path = f"data_adherence/{name}.jsonl"
    rows = [json.loads(l) for l in open(path)]
    lens = sorted(raw_chars(r) for r in rows)
    n = len(lens)
    pct = lambda p: lens[min(int(n * p), n - 1)]
    kept = [r for r in rows if raw_chars(r) <= CAP]
    dropped = n - len(kept)
    with open(path, "w") as f:
        for r in kept:
            f.write(json.dumps(r) + "\n")
    print(f"{name}: chars p50={pct(.5)} p90={pct(.9)} p99={pct(.99)} max={lens[-1]}")
    print(f"       kept {len(kept)}/{n}  (dropped {dropped} over {CAP} chars)")
