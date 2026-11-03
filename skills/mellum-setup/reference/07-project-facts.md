# Phase 8: Project facts for Mellum Worker (optional)

Why: on the ladder's four AgentClinic rungs (build a small FastAPI app from
loose phase specs, 12 runs per condition), Mellum Worker passed 9 of 12 runs
with this section and 1 of 12 without it (rescored under the added-tests
rule; 0 of 12 under the strict rule that run used), at a median of 26
requests against 50.

Pi Mode only: Mode is what reads the section, so a session not running Mode
skips this phase. Like phase 6, this is always a question, never an
automatic write: AGENTS.md belongs to the user's project. It applies to
the project the user runs `pi` in (Mode reads `AGENTS.md` from that
working directory), not to `$PKG`.

Check: the project's `AGENTS.md` already has a heading that is exactly
`## Mellum`, or the user declined. Phase 6's `## Mellum Worker` heading
does not count; Mode reads only the exact heading.

```bash
grep -niE '^##[[:space:]]+Mellum[[:space:]]*$' AGENTS.md
```

Ask: "Do you want a `## Mellum` section in this project's AGENTS.md, so
Mellum Worker is told the project's test command?"

If yes:

1. Ask for the test command: the one that runs the project's tests from
   its root, exactly as typed. If the user is unsure, offer to run their
   candidate once and show the result; a command that cannot import the
   project's code is what this section prevents. For a project whose
   `pyproject.toml` mentions pytest, Mode already falls back to
   `uv run --offline python -m pytest -q` when the section names no test
   command; say so. Write the label as plain `Test command:` and the
   command as plain text: Mode recognises the test command only from a
   bullet whose label is exactly `Test command:` (no bold or code
   formatting on the label or the command). `- **Test command:** make test`
   is not recognised, so in a pytest project Mode would add the fallback as
   a second test command, and a backticked command keeps its backticks.
2. Offer a `Do not:` line naming what Mellum should leave alone, for
   example: install packages or add dependencies; add `__init__.py`,
   `conftest.py`, `pytest.ini` or `setup.cfg` files; weaken tests. Name the
   files, not "the project root": many projects keep code there. Mention, without pushing it, that a `Write only:`
   line (the files and directories Mellum may change) gives a strict
   boundary; the measured section had one, but most projects do not need
   it.
3. Show the section, filled in, for example:

```markdown
## Mellum

- Test command: uv run python -m pytest tests
- Do not: install packages or add dependencies; add __init__.py, conftest.py, pytest.ini or setup.cfg files; weaken tests
```

4. Ask before writing. On a yes, append it to the end of `AGENTS.md`
   (create the file if absent). Mode reads only bullets, one line each
   (it drops continuation lines and flattens nested bullets), and the
   section ends at the next `#` or `##` heading. Keep the bullet text to at
   most 600 characters; over that, Mode warns and ignores the whole section.
5. If `pyproject.toml` mentions pytest, has no `pythonpath` under
   `[tool.pytest.ini_options]`, and the tests import modules from the
   project root, offer to add `pythonpath = ["."]` there, so every way of
   running the tests (bare `pytest`, `uv run pytest`, `python -m pytest`)
   can import them. Show the lines and ask before writing.

If no, record that the user declined and move on.

Tell the user: the next `/mellum` in that project shows
`[mellum-mode on] facts: agents-md` (or `agents-md+detected` when the
section has no test command and the fallback was added), and the handoff
summary line names the same source. `MELLUM_MODE_FACTS=0` in the
environment turns the section and the fallback off.
