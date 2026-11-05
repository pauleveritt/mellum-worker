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
    qualified = (len(requests) == 1 and len(messages) == 1 and messages[0].get("stopReason") == "stop"
        and messages[0].get("usage", {}).get("output", 0) > 0
        and harness.execution_outcome(run)["completion"] == "settled"
        and requests[0]["payload"].get("max_tokens") == 16384
        and requests[0]["payload"].get("temperature") == 1
        and requests[0]["payload"].get("top_p") == .95)
    write_json(output / "qualification.json", {"qualified": qualified, "run": str(run), "image": image})
    return qualified
