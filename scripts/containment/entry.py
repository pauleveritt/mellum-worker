"""Trusted container entry; no host paths, inherited credentials or grader in model mode."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/opt/instrument/learn/code")
import harness
from containment import agent_environment

os.environ.clear()
os.environ.update(agent_environment())

data = json.loads(Path("/attempt/input.json").read_text())
suite = harness.Suite(**data["suite"], tests=Path("/attempt/grader"),
                      root=Path("/attempt/suite"),
                      start=Path("/attempt/suite/start") if Path("/attempt/suite/start").is_dir() else None)
if sys.argv[1] == "model":
    harness.run_suite(suite, runs_dir=Path("/attempt/runs"), profile=Path("/attempt/profile"),
                      pi_binary="/usr/local/bin/pi", **data["options"])
else:
    run = Path("/attempt/grading")
    versions = data.get("versions") or {"ruff":"0.16.3", "complexipy":"8.3.0", "pyrefly":"1.2.0", "pytest":"8.3.4"}
    grades = harness.grade(run / "workspace", versions=versions)
    scored = harness.score_details(run, suite, versions=versions)
    (run / "result.json").write_text(json.dumps({"grades":grades, "scored":scored}))
