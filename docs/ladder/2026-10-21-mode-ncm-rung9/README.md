# 2026-10-21: `--acceptance-test` in Mode cracks rung 9 — 0/3 → 3/3

**What is measured.** 6-bit Mellum in **Mellum Mode** (`mellum-mode.ts` +
`mellum-guards.ts` + `mellum-facts.ts`, as shipped), rung 9, n=3, with two named
mechanisms added — not lumped as "mediation":

- **`--acceptance-test`** (a `run_ladder` flag, now allowed in `--mode mode`):
  places the frozen `test_phase4.py` in the Mode workspace.
- **`mellum-ncm.ts`** (the NCM verify gate, loaded via `--pi-extension`, which
  the mode runner now forwards): re-runs the named test at settle and, while
  red, sends the worker back on the unmet concepts.

Result (`table.md`): **3/3** (110/145/108s), up from the shipped Mode's **0/3**
with neither mechanism.

**Credit by name.** **`--acceptance-test` is the lever** — placing the frozen
test gives v7 its named target. **`mellum-ncm.ts` fired 0 times** (the 6-bit
passes first-try), so it is a non-regressing safety net here, not the driver;
`mellum-mode.ts`/`guards`/`facts` were on in both the 0/3 and 3/3 runs.

Note: [`research/2026-10-21-acceptance-test-in-mode.md`](../../superpowers/research/2026-10-21-acceptance-test-in-mode.md).
Raw stripped per `AGENTS.md`.
