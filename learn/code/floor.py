"""The Vanilla floor's preregistered rules (LC.39).

Validity, replacement, the LC.34 usable rule and the portability reading, as fixed in
docs/superpowers/research/2026-11-05-portable-floor-preregistration.md. Pure apart
from reading a run directory.
"""
import json
from pathlib import Path

import rig
from acceptance_budget import wilson

PLAN = {"A": 6, "B": 6, "M": 3}
CUDA_HOSTS = ("A", "B")
MAX_REPLACEMENTS = 2
PORTABILITY_GAP = 4          # 0/6 against 4/6: Fisher two-sided p = 0.061
BUDGET_ENDINGS = 3


def card_usable(card: dict, pins: dict) -> tuple[bool, str]:
    if not card.get("passed"):
        return False, "host card did not pass conformance"
    if card.get("pins_digest") != rig.pins_digest(pins):
        return False, "host card predates the current pin card"
    return True, ""


def transport_recovered(proxy_rows: list[dict], completion: str) -> bool:
    """A transport error counts as recovered when Pi carried on to a model outcome."""
    errors = [row for row in proxy_rows if row.get("boundary") in ("stream_error", "request_error")]
    return not errors or completion in ("settled", "stalled", "budget")


def validity(execution: dict, budget: dict, sweep: dict, recovered: bool, post_check: str) -> tuple[str, str]:
    if execution.get("termination_reason") == "wall_safety":
        return "invalid", "reached the wall safety net"
    if not budget.get("reconciled"):
        return "invalid", "server generations do not reconcile with proxy requests: " + "; ".join(budget.get("issues", []))
    if not recovered:
        return "invalid", "unrecovered transport error"
    if not sweep.get("ok"):
        return "invalid", "sweep or preflight failed"
    if not execution.get("cleanup_ok", True):
        return "invalid", "cleanup failed"
    if post_check == "failed":
        return "invalid", "host failed the post-cohort conformance check"
    if post_check == "unavailable":
        return "counted", "post-check unavailable"
    return "counted", ""


def may_replace(host_state: dict) -> bool:
    return host_state.get("replacements", 0) < MAX_REPLACEMENTS


def _json(path: Path):
    return json.loads(path.read_text()) if path.is_file() else None


def session_record(run: Path, card: dict) -> dict:
    run = Path(run)
    record = _json(run / "run.json") or {}
    acceptance = (_json(run / "acceptance.json") or {}).get("result", {})
    layout = _json(run / "layout.json") or {"out_of_layout": []}
    budget = _json(run / "budget.json") or {"reconciled": False}
    proxy = [json.loads(line) for line in (run / "proxy.jsonl").read_text().splitlines() if line.strip()] \
        if (run / "proxy.jsonl").is_file() else []
    checks = {name: bool(check.get("passed")) for name, check in acceptance.get("checks", {}).items()}
    hidden_all_pass = bool(record.get("checks_ran")) and record.get("checks_passed") == record.get("checks_total")
    max_tokens = [row.get("max_tokens") for row in proxy if row.get("boundary") == "rewritten"]
    pinned = rig.load_pins()["client"]["max_tokens"]
    usable = (acceptance.get("status") == "pass" and hidden_all_pass and record.get("code_health") == "pass"
              and record.get("completion") == "settled" and not layout.get("out_of_layout"))
    return {"run": str(run), "rental_id": card.get("rental_id"), "uncontained": bool(acceptance.get("uncontained")),
            "completion": record.get("completion"), "checks_ran": record.get("checks_ran"),
            "checks_passed": record.get("checks_passed"), "checks_total": record.get("checks_total"),
            "missing_checks": record.get("missing_checks", []), "hidden_all_pass": hidden_all_pass,
            "code_health": record.get("code_health"), "out_of_layout": layout.get("out_of_layout", []),
            "acceptance_status": acceptance.get("status"), "acceptance_checks": checks,
            "usable": usable, "budget": budget,
            "max_tokens_sent": sorted(set(max_tokens), key=lambda v: (v is None, v)),
            "max_tokens_as_pinned": all(value == pinned for value in max_tokens)}


def _count(rows: list[dict], key) -> int:
    return sum(1 for row in rows if key(row))


def portability(a: list[dict], b: list[dict]) -> dict:
    components = {"hidden_all_pass": lambda r: r.get("hidden_all_pass"),
                  "startup": lambda r: r.get("acceptance_checks", {}).get("startup"),
                  "settled": lambda r: r.get("completion") == "settled"}
    reasons = []
    for name, key in components.items():
        gap = abs(_count(a, key) - _count(b, key))
        if gap >= PORTABILITY_GAP:
            reasons.append(f"{name} differs by {gap} of {max(len(a), len(b))}")
    budget_a, budget_b = (_count(rows, lambda r: r.get("completion") == "budget") for rows in (a, b))
    if (budget_a >= BUDGET_ENDINGS and budget_b == 0) or (budget_b >= BUDGET_ENDINGS and budget_a == 0):
        reasons.append(f"budget endings {budget_a} against {budget_b}")
    return {"portable": not reasons, "reasons": reasons}


def _table(rows: list[dict]) -> dict:
    usable = _count(rows, lambda r: r.get("usable"))
    return {"n": len(rows), "usable": usable, "wilson_95": wilson(usable, len(rows)),
            "uncontained": any(r.get("uncontained") for r in rows)}


def summarize_floor(records: list[dict]) -> dict:
    hosts = sorted({r["host"] for r in records}, key=lambda h: (h not in PLAN, list(PLAN).index(h) if h in PLAN else 0))
    return {"per_host": {host: _table([r for r in records if r["host"] == host]) for host in hosts},
            "pooled_cuda": _table([r for r in records if r["host"] in CUDA_HOSTS]),
            "pooled_all": _table(records)}
