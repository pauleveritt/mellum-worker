# AgentClinic fixtures (rungs 6-9)

Four rungs built from the four phases of the AgentClinic demo
(`ac-demo`, HEAD `f64d4e316fc664dfa15dd44e01de3dd6109d768a`). Each rung hands
Mellum one looser phase spec and asks it to implement it in a small FastAPI
project that already holds the earlier phases. This directory has no
workspace of its own; it only documents the others.

| Directory | What it is |
| --- | --- |
| `agentclinic-p1/` | start of phase 1: `pyproject.toml`, `uv.lock`, `AGENTS.md`, `specs/phase-1-home.md`, empty `tests/` |
| `agentclinic-p2/` | start of phase 2: the phase 1 solution plus `specs/phase-2-board.md` |
| `agentclinic-p3/` | start of phase 3: phases 1-2 solved plus `specs/phase-3-add.md` |
| `agentclinic-p4/` | start of phase 4: phases 1-3 solved plus `specs/phase-4-resolve-reopen.md` |
| `agentclinic-done/` | all four phases solved (the reference end state) |
| `agentclinic-hidden/` | `_hidden_p1.py` ... `_hidden_p4.py`, the behaviour tests a rung is scored on |
| `agentclinic-given/` | `test_phase4.py`: a developer's Phase 4 test written from the bullets; `--given-test` copies it into `tests/` before the baseline and appends `; make tests/test_phase4.py pass` to the task (the M.11 screen) |

`pyproject.toml` and `uv.lock` are copied from ac-demo HEAD unchanged
(`fastapi[standard]==0.115.10`, pinned). Every `AGENTS.md` carries only the
`## Mellum` facts section. The spec's Appendix A holds the verbatim text of
the looser specs and that section.

## Authoring rules

From each original phase spec (spec section 2 of the M.7 design):

- Drop every coding hint: imports, `field(default_factory=...)`, `Form`,
  `RedirectResponse`, "insert alongside the existing route".
- Keep a file or symbol name only where a hidden test imports it or a later
  phase depends on it: `app.py`'s `app`, `models.py`'s `Complaint` and
  `complaints`, `templates/base.html`.
- Drop the per-phase rules paragraph (dependencies, write-only paths, the
  test command); it lives in `AGENTS.md`.
- Keep every testable behaviour, in plain words.

Also dropped: the test and template file names other than
`templates/base.html`, "create the `templates/` directory" and
`{% block content %}`.

## Fact count per phase

One fact per bullet clause that states a requirement. A hint such as the
`dataclasses` import counts as a clause in the original and is gone in the
looser spec. The per-phase rules paragraph is not a bullet and is counted on
neither side.

| Phase | Original | Looser | Fewer |
| --- | --- | --- | --- |
| 1 Home page | 23 | 18 | 22% |
| 2 Complaints board | 25 | 16 | 36% |
| 3 Add complaint | 15 | 10 | 33% |
| 4 Resolve and reopen | 27 | 14 | 48% |
| All four | 90 | 58 | 36% |

The target was about 25% fewer per phase. Phase 1 lands just under it, the
others well over; phase 4 loses the most because its original spells out the
id mechanics.

## Self-check

`ladder/tests/test_agentclinic_fixture.py` (marked `slow`) copies each state to
a scratch directory, runs `uv sync --offline` (it must exit 0), and asserts
that every start state fails its phase's hidden tests while the next state
passes the hidden tests of phases 1..N together with its own tests. Never
`uv sync` inside the fixture directories: the `.venv` would be copied into
every run.
