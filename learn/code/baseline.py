"""Provenance and compact reporting for the trusted Vanilla collection."""


def render_scorecard(records: list[dict]) -> str:
    lines = ["| Run | Hidden checks | Code health | Completion | Model turns | Output tokens | Elapsed seconds |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for record in records:
        checks = f"{record.get('checks_passed', 0)}/{record.get('checks_total', 0)}"
        if not record.get("checks_ran"):
            checks = f"not run ({checks})"
        values = [record.get("run_id", "unknown"), checks,
                  record.get("code_health", "not checked"), record.get("completion", "error"),
                  record.get("turns"), record.get("output_tokens"), record.get("elapsed_seconds")]
        lines.append("| " + " | ".join("unknown" if value is None else str(value).replace("|", "\\|")
                                      for value in values) + " |")
    return "\n".join(lines) + "\n"
