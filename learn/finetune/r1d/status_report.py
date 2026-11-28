"""Write a Markdown status report of the small-model work, for reading from another machine.

    uv run --no-project python r1d/status_report.py > out/STATUS.md
"""
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

FT = Path(__file__).resolve().parents[1]
REPO = FT.parents[1]
STATE = FT / "out" / "status-state.json"
LOG = FT / "out" / (json.loads(STATE.read_text()).get("log", "none") if STATE.is_file() else "none")
STEPS = [
    ("Calls that parse: llama.cpp returns a structured tool call when one is due", "next"),
    ("Calls that are right: faulty calls per 100, tool choice, valid arguments", "later"),
    ("BFCL (well-known tool-calling benchmark, held out from training)", "later"),
    ("End to end: the Easy screen against the untrained model", "later"),
]
TRAIN = re.compile(r"\[train\] update (\d+)/(\d+): loss ([\d.]+) \| ([\d.]+) min, ~(\d+) min left, peak ([\d.]+) GB")


def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO).stdout.strip()


def state():
    if not STATE.is_file():
        return []
    st = json.loads(STATE.read_text())
    return [f"- **Now:** {st.get('now', '')}"] + [f"- {x}" for x in st.get("notes", [])]


def training():
    if not LOG.is_file() :
        return ["No training running."]
    if not LOG.is_file():
        return ["No training log yet."]
    text = LOG.read_text(errors="ignore")
    rows = [m.groups() for m in TRAIN.finditer(text)]
    evals = [json.loads(line.split("[eval] ", 1)[1]) for line in text.splitlines() if line.startswith("[eval] ")]
    out = ["- **Job:** supervised training of DeepSeek-R1-Distill-Qwen-1.5B (LoRA + only the new token rows), log `" + LOG.name + "`."]
    if "TRAINING DONE" in text:
        out.append("- **State:** finished.")
    elif "Traceback" in text:
        out.append("- **State:** FAILED, see the log tail below.")
    elif rows:
        u, n, loss, mins, left, peak = rows[-1]
        out.append(f"- **State:** update {u} of {n} ({int(u) * 100 // int(n)}%), {float(mins):.0f} min elapsed, "
                   f"about {left} min left, peak memory {peak} GB.")
    else:
        out.append("- **State:** starting (evaluating the untrained model first).")
    if rows:
        losses = [float(r[2]) for r in rows]
        first, last = losses[:10], losses[-10:]
        out.append(f"- **Training loss:** first {len(first)} updates average {sum(first) / len(first):.3f}; "
                   f"last {len(last)} average {sum(last) / len(last):.3f}.")
    if evals:
        out += ["", "| Update | Validation loss | Marker hit rate |", "|---|---|---|"]
        out += [f"| {e['update']} | {e['val_loss']:.3f} | {e['marker_hits']}/{e['marker_positions']} "
                f"({e['marker_rate']:.0%}) |" for e in evals]
        out += ["", "Marker hit rate: of the held-out positions where a tool call starts, how often the model ranks "
                "`<｜tool▁calls▁begin｜>` first. Update 0 is the untrained model."]
    if "Traceback" in text:
        out += ["", "```", "\n".join(text.splitlines()[-15:]), "```"]
    return out


def jobs():
    ps = sh("ps", "-axo", "command")
    found = []
    for pattern, label in [("r1d/train_sft.py", "1.5B training"), ("llama-server", "llama-server"),
                           ("harness.py run", "harness run (screen)"), ("publish_hf.py", "Hugging Face publish")]:
        if pattern in ps:
            found.append(label)
    return found or ["nothing running"]


def main():
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [f"# Small-model status", "", f"Updated {now}. Refreshed every 10 minutes.", "",
             "**Target:** good tool calling, added to a model that lacks it, by a method that works on any model "
             "([ADR 0010](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/adr/0010-the-target-is-tool-calling.md)).",
             "", "## Running now", ""] + [f"- {j}" for j in jobs()]
    lines += ["", "## Current phase", ""] + state() + ["", "## Training", ""] + training()
    lines += ["", "## The proof, step by step", "", "| Step | Status |", "|---|---|"]
    lines += [f"| {i}. {s} | {st} |" for i, (s, st) in enumerate(STEPS, 1)]
    lines += ["", "## Already shown", "",
              "- DeepSeek's nine tool markers are real single tokens in the 1.5B (spare rows 151665-151673), "
              "proven in the tokenizer, transformers and llama.cpp.",
              "- Smoke run, 40 examples: marker hit rate 0/10 before, 10/10 after 10 updates.",
              "- The lab Mellum (vLLM) works as the teacher through the harness, in the student's harness shape.",
              "- Tsunami (Mellum 12B tune) is uploaded to Hugging Face, private.",
              "", "## Latest commits", "", "```", sh("git", "log", "--oneline", "-8"), "```",
              "", "Record: [research note](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-28-tool-tokens-1-5b.md)"
              " · [plan](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/plans/2026-11-28-r1d-tool-tokens.md)"
              " · [ADRs](https://github.com/andrevanzuydam/mellum-worker/tree/main/docs/adr)"]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
