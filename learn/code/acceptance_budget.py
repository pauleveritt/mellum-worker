"""Whole-task inference accounting independent of Pi's ordinary-turn hooks."""
import math
import re
import statistics
from datetime import datetime


def moment(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() if value else 0


def reconcile(log: str, relay: list[dict], trace: list[dict], receipts: list[dict]) -> dict:
    tasks = {}
    order = []
    for match in re.finditer(r"slot\s+operator\(\): id\s+\d+ \| task (\d+) \| new prompt, .*task.n_tokens = (\d+)", log):
        tasks[int(match[1])] = {"task": int(match[1]), "full_prompt_tokens": int(match[2])}
    for match in re.finditer(r"slot print_timing: id\s+\d+ \| task (\d+) \| prompt eval time\s*=\s+[\d.]+ ms /\s+(\d+) tokens", log):
        tasks.setdefault(int(match[1]), {"task": int(match[1])})["evaluated_prompt_tokens"] = int(match[2])
    for match in re.finditer(r"slot print_timing: id\s+\d+ \| task (\d+) \|\s+eval time\s*=\s+[\d.]+ ms /\s+(\d+) tokens", log):
        tasks.setdefault(int(match[1]), {"task": int(match[1])})["output_tokens"] = int(match[2])
        order.append(int(match[1]))
    created = [row for row in relay if row.get("boundary") == "created"
               and row.get("method", "POST") == "POST" and row.get("path", "/v1/chat/completions") == "/v1/chat/completions"]
    issues = []
    if len(order) != len(created) or len(tasks) != len(order) or len(set(order)) != len(order):
        issues.append("server generations do not reconcile with relay-created inference requests")
    if len({r["id"] for r in created}) != len(created):
        issues.append("duplicate relay identities")
    generations = []
    for boundary, task in zip(created, order):
        generations.append({**tasks[task], "relay_id": boundary["id"],
            "repair_index": sum(r.get("continue") is True and moment(r.get("timestamp")) <= moment(boundary.get("timestamp"))
                                for r in receipts)})
    agent_requests = [r for r in trace if r.get("type") == "provider_request"]
    messages = [r for r in trace if r.get("type") == "message_end" and r.get("message", {}).get("role") == "assistant"]
    usage_known = bool(messages) and all(m["message"].get("stopReason") not in {"error", "aborted"}
        and type(m["message"].get("usage", {}).get("output")) is int for m in messages)
    agent_output = sum(m["message"]["usage"]["output"] for m in messages) if usage_known else None
    output = sum(t["output_tokens"] for t in generations) if not issues else None
    if len(agent_requests) == len(created) and agent_output is not None and output != agent_output:
        issues.append("agent successful output differs from backend timing output")
        output = None
    return {"requests": len(created), "agent_requests": len(agent_requests),
            "outside_agent_requests": len(created) - len(agent_requests),
            "agent_output_tokens": agent_output, "output_tokens": output,
            "reconciled": not issues, "issues": issues, "generations": generations,
            "compaction_attempts": sum(r.get("type") == "before_compact" for r in trace),
            "compaction_completed": sum(r.get("type") == "compact_complete" for r in trace),
            "compaction_usage": [r.get("usage") for r in trace if r.get("type") == "compact_complete"]}


def wilson(passed: int, total: int) -> tuple[float, float]:
    if not total:
        return 0.0, 1.0
    z = 1.959963984540054
    p = passed / total; denominator = 1 + z * z / total
    midpoint = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, midpoint - half), min(1.0, midpoint + half)


def summarize(records: list[dict]) -> dict:
    usable = sum(r["usable"] for r in records)
    requests = sum(r["budget"]["requests"] for r in records)
    known = all(r["budget"]["reconciled"] and r["budget"]["output_tokens"] is not None for r in records)
    output = sum(r["budget"]["output_tokens"] for r in records) if known else None
    return {"n": len(records), "usable": usable, "wilson_95": wilson(usable, len(records)),
            "requests": requests, "output_tokens": output,
            "requests_per_usable": requests / usable if usable else None,
            "output_per_usable": output / usable if usable and output is not None else None,
            "requests_median": statistics.median(r["budget"]["requests"] for r in records) if records else None,
            "output_median": statistics.median(r["budget"]["output_tokens"] for r in records) if records and known else None,
            "reconciled": known}
