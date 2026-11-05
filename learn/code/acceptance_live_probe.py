"""One short uncounted native Pi generation through the frozen local backend."""
import json
from pathlib import Path

import harness
from baseline import write_json
from containment import run_contained


def qualify(image: str, profile: Path, output: Path) -> bool:
    suite = harness.Suite(name="live-qualification", prompts=["Reply briefly with ready."], tests=output / "no-grader", start=None)
    run = run_contained(suite, image=image, runs_dir=output, profile=profile, arm="vanilla", deadline=90, stall=30)
    rows = [json.loads(line) for line in (run / "trace.jsonl").read_text().splitlines()]
    requests = [r for r in rows if r.get("type") == "provider_request"]
    messages = [r["message"] for r in rows if r.get("type") == "message_end" and r.get("message", {}).get("role") == "assistant"]
    expected = {"model": "Mellum2.1-12B-A2.5B-Thinking", "max_tokens": 16384,
        "temperature": 1, "top_p": .95, "top_k": 20, "min_p": 0,
        "presence_penalty": 0, "repetition_penalty": 1,
        "chat_template_kwargs": {"enable_thinking": True, "preserve_thinking": True}}
    qualified = (len(requests) == 1 and len(messages) == 1 and messages[0].get("stopReason") == "stop"
        and messages[0].get("usage", {}).get("output", 0) > 0
        and harness.execution_outcome(run)["completion"] == "settled"
        and all(requests[0]["payload"].get(key) == value for key, value in expected.items()))
    write_json(output / "qualification.json", {"qualified": qualified, "run": str(run), "image": image})
    return qualified
