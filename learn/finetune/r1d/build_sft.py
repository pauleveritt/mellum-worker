"""Supervised examples for the 1.5B distill, in DeepSeek's tool-call format (r1d/deepseek_tools.jinja).

Each example is one assistant step from a phase that passed its hidden tests in a recorded Mellum run:
`prompt` is the conversation up to that step, rendered with the template and ending in `<｜Assistant｜><think>\n`;
`completion` is the step's own thinking, `</think>`, its text and its tool calls. History keeps no thinking, as
at inference. A step whose own call failed (a missing file, an edit that matched nothing, a malformed shell
command) is not taught; a red test run is normal work and is kept. Phase 1 stays out (`--exclude 1`): the Easy
screen is phase 1. Validation rows are held out by whole run.

    uv run --no-project --with jinja2 --with tokenizers python r1d/build_sft.py \
        --source ../../runs/<dir> ... --tokenizer ~/models/r1d-1.5b/hf-tooltokens --out r1d/data_sft_v1
"""
import argparse
import collections
import glob
import json
import sys
from pathlib import Path

import jinja2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
TEMPLATE = (HERE / "deepseek_tools.jinja").read_text()
BOS = "<｜begin▁of▁sentence｜>"
_env = jinja2.Environment()
_env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
_tpl = _env.from_string(TEMPLATE)


EVAL_TASKS = {d.name for d in (HERE.parents[1] / "code" / "suites" / "py-features").iterdir() if d.is_dir()}


def held_out(suite):
    """Never train on these (ADR 0010): the AgentClinic family and the Python eval tasks."""
    suite = str(suite)
    return suite in ("easy", "medium", "hard") or "agentclinic" in suite or suite in EVAL_TASKS


def render(messages, tools, gen=False, thinking=True):
    return _tpl.render(messages=messages, tools=tools, add_generation_prompt=gen, bos_token=BOS,
                       enable_thinking=thinking)


def examples(msgs, scored, tools, failed, modes=("on", "off")):
    """[{step, mode, prompt, completion}] for each scored assistant index not in `failed`, once per thinking mode.

    `on`: the prompt opens thinking and the completion is the step's thinking, `</think>`, then its text and calls.
    `off`: the prompt closes an empty thinking block and the completion is the same text and calls (ADR 0012)."""
    out = []
    for i in scored:
        if i in failed:
            continue
        plain = {k: v for k, v in msgs[i].items() if k != "reasoning_content"}
        before, whole = render(msgs[:i], tools), render(msgs[:i] + [plain], tools)
        assert whole.startswith(before + "<｜Assistant｜>"), "template is not prefix-stable"
        tail = whole[len(before) + len("<｜Assistant｜>"):]
        thinking = (msgs[i].get("reasoning_content") or "").strip()
        for mode in modes:
            prompt = render(msgs[:i], tools, gen=True, thinking=mode == "on")
            completion = f"{thinking}\n</think>\n\n{tail}" if mode == "on" else tail
            out.append({"step": i, "mode": mode, "prompt": prompt, "completion": completion})
    return out


def _bad_call(err):
    from pathology_pairs import shell_shape
    name, is_error, text = err
    return is_error and (name != "bash" or shell_shape(text) is not None)


def main():
    from tokenizers import Tokenizer
    from pairs_io import write_pairs
    from phase_pairs import best_outcomes, grader_seen, phase_outcomes, render_segment, segment_trace
    from pathology_pairs import with_regressions

    ap = argparse.ArgumentParser()
    ap.add_argument("--source", action="append", default=[])
    ap.add_argument("--source-all-phases", action="append", default=[])
    ap.add_argument("--exclude", type=int, action="append", default=[1])
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--budget", type=int, default=24576, help="max tokens per example; longer ones are dropped")
    ap.add_argument("--valid-every", type=int, default=10, help="every Nth run goes to validation")
    ap.add_argument("--cap", choices=["none", "head-tail"], default="none",
                    help="none: keep tool results as the harness recorded them (teacher runs are already trimmed by "
                         "context/trim-tool-output); head-tail: the old 400+200 cut, kept only to rebuild v1")
    ap.add_argument("--head", type=int, default=400)
    ap.add_argument("--tail", type=int, default=200)
    ap.add_argument("--all-runs", action="store_true",
                    help="also teach successful steps from phases that failed their hidden tests (ADR 0010)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} exists: build into a new folder")
    tok = Tokenizer.from_file(str(Path(args.tokenizer).expanduser() / "tokenizer.json"))

    def cap(text):
        if args.cap == "none":
            return text
        if len(text) <= args.head + args.tail + 40:
            return text
        return text[:args.head] + f"\n...[{len(text) - args.head - args.tail} chars elided]...\n" + text[-args.tail:]

    why, rows, n_runs = collections.Counter(), {"train": [], "valid": []}, 0
    for root, keep_all in [(r, False) for r in args.source] + [(r, True) for r in args.source_all_phases]:
        for f in sorted(glob.glob(f"{root}/**/run.json", recursive=True)):
            run, trace = json.load(open(f)), Path(f).with_name("trace.jsonl")
            if held_out(run.get("suite")):
                why["held-out-suite"] += 1
                continue
            if run.get("contaminated") and trace.is_file():
                canary_file = HERE.parents[1] / "code" / "suites" / str(run.get("suite")) / "grader" / "canary"
                canary = canary_file.read_text().strip() if canary_file.is_file() else None
                if not grader_seen(trace.read_text(errors="ignore"), run.get("suite"), canary):
                    run = {**run, "contaminated": False}
            outcome = phase_outcomes(run)
            if run.get("contaminated") or not trace.is_file() or (not outcome and not args.all_runs):
                why["contaminated-no-trace-or-grade"] += 1
                continue
            segs = segment_trace([json.loads(x) for x in open(trace) if x.strip()])
            pg, pr = Path(f).with_name("phase_grades.json"), Path(f).with_name("phase_regressions.json")
            outcome = best_outcomes(outcome, json.loads(pg.read_text()) if pg.is_file() else None, reached=len(segs))
            outcome = with_regressions(outcome, json.loads(pr.read_text()) if pr.is_file() else None)
            n_runs += 1
            split = "valid" if n_runs % args.valid_every == 0 else "train"
            for seg in segs:
                p = seg["phase"]
                if (not keep_all and p in args.exclude) or (not outcome.get(p) and not args.all_runs):
                    continue
                rendered = render_segment(seg, cap=cap)
                if rendered is None:
                    why["misaligned"] += 1
                    continue
                msgs, scored = rendered
                ast, n_acts = [i for i, m in enumerate(msgs) if m["role"] == "assistant"], len(seg["acts"])
                act_of = {ast[-j]: n_acts - j for j in range(1, len(ast) + 1)}
                failed = {i for i in scored if any(_bad_call(e) for e in (seg.get("errs") or {}).get(act_of[i], []))}
                why["failed-step-skipped"] += len(failed)
                for ex in examples(msgs, scored, seg["payload"].get("tools"), failed):
                    n = len(tok.encode(ex["prompt"] + ex["completion"], add_special_tokens=False).ids)
                    if n > args.budget:
                        why["over-budget"] += 1
                        continue
                    rows[split].append({"prompt": ex["prompt"], "completion": ex["completion"], "tokens": n,
                                        "phase": f"{run.get('suite')}:p{p}", "passed": bool(outcome.get(p)), "mode": ex["mode"],
                                        "src": f"{Path(f).parent.name}#p{p}#{ex['step']}#{ex['mode']}"})
                    why["ok"] += 1
    print("examples:", dict(why))
    for split, r in rows.items():
        write_pairs(out, split, r)
        print(split, len(r), "examples,", sum(x["tokens"] for x in r), "tokens")


if __name__ == "__main__":
    main()
