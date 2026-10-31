# AgentClinic — agent notes

A small FastAPI + Jinja2 complaints app. The phased requirements are in
specs/roadmap.md.

## Mellum

- Test command: uv run --frozen python -m pytest tests
- Run Python commands with uv run --frozen.
- Use existing dependencies and test configuration.
- Keep changes scoped to the task; do not weaken existing tests.
- Before reporting completion, run the test command and report its result.
- Do not: start servers
