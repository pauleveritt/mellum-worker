# Flow harness — architecture map

How the spec-driven flow drives the FIXED model (Mellum 2.1, 6-bit via oMLX)
through a suite, and where the harness guarantees sit. The agent lives in Pi
(TypeScript); the Python layer wraps it with the orchestration and grading that
don't depend on the model behaving.

```mermaid
flowchart TB
    subgraph DRV["PYTHON DRIVER — flow_run.py (the lab bench, not the agent)"]
        A["load suite + copy base workspace<br/>(app scaffold, data.db fixture, specs)"] --> B["pin models.json<br/>--context-window, model, base_url"]
        B --> C["decompose spec into 7 phases"]
        C --> LOOP{"for each phase 1..7<br/>(SEQUENTIAL — each builds on the last)"}
    end

    LOOP -->|"spawn pi (orchestrator) — subprocess"| ORCH

    subgraph ORCH["PI AGENT — extensions/mellum-flow.ts (phases-as-tools)"]
        direction LR
        PLAN[plan] --> RPLAN[review_plan] --> EXAM["examine<br/>writes the acceptance test"] --> CODE[code] --> RCODE[review_code] --> TEST[test]
    end

    EXAM -.->|freeze| GATE[("plan/gate/phase_N.py<br/>frozen gate = definition of DONE")]
    ORCH -->|"each tool = an isolated pi sub-agent"| MODEL[["Mellum 2.1 6-bit<br/>via oMLX :8001 (fixed model)"]]

    ORCH --> SCORE{"score THIS phase"}
    GATE -.->|restore_gate| SCORE
    SCORE -->|"run_gate(phase N only) + phase_gate_ok"| PASS{"pass?"}
    PASS -->|"no — retry up to 4 rounds<br/>(best-of-N forks at --concurrency>1)"| LOOP
    PASS -->|yes| LOOP

    LOOP ==>|"all 7 phases done"| FIX["restore_fixture_data<br/>put pristine fixture rows back<br/>(keep migrated schema)"]
    FIX --> HIDDEN["score_workspace<br/>HIDDEN grader = suite's OWN tests<br/>(never the examiner's gates)"]
    HIDDEN --> VERDICT["visible= / hidden-grader=<br/>the real measure"]

    classDef fix fill:#1f6f43,stroke:#9be7b4,color:#eafff0;
    classDef gate fill:#5a3b8c,stroke:#c9b3f0,color:#f3ecff;
    classDef model fill:#8a4b1f,stroke:#f0c39b,color:#fff2e6;
    class FIX,HIDDEN fix;
    class GATE gate;
    class MODEL model;
```

## How to read it

- **Python driver (`flow_run.py`)** sets the task, pins the model profile, splits
  the spec into 7 phases, and loops them **sequentially** (phase 6 builds on 5).
- **Pi agent (`extensions/mellum-flow.ts`)** runs the phase as tools —
  `plan → review_plan → examine → code → review_code → test` — each an isolated
  `pi` sub-agent calling the fixed model. `examine` **freezes** the acceptance
  gate; `code` must make it pass.
- **Per-phase scoring:** `run_gate(phase N only)` + `phase_gate_ok` — a phase
  passes on **its own** gate, so a stochastically-brittle earlier gate can't
  cascade into later phases. Retry up to 4 rounds; best-of-N forks when
  `--concurrency > 1`.
- **Final grade:** `restore_fixture_data` restores the pristine fixture rows
  (keeping the coder's migrated schema), then `score_workspace` runs the suite's
  **hidden** grader — never the examiner's gates. That is the real measure.

## The load-bearing idea

The model builds the app; the harness only wraps it. The durable wins are the
Python-side **guarantees** — per-phase scoring (don't block a correct build),
fixture restore (don't corrupt the data it's graded on), schema injection (prime
it with the real columns), best-of-N (more tries) — none of which write code.
The remaining gap on the database phases is the model's build quality, which the
harness can raise the odds on but cannot manufacture.
