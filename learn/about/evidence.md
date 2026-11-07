# Evidence and Badges

Each step of a lesson (except the Interpretation) opens with an evidence badge. The badge tells you what the step rests on, from a preregistered run to a reasoned conjecture.

![Four coloured badges on a table, green, blue, amber and grey, examined by a small robot](../assets/illustrations/evidence.webp){ .illustration }

## Badges

| Badge | Means | Needs |
| --- | --- | --- |
| `reference-run` | A preregistered run on llama.cpp, made for this lesson, on the suites the course teaches | A preregistration written before the run naming the lesson, the arms, n, the reading and the decision rule; the record in `docs/superpowers/research/`; raw evidence in a `research-*` release; machine and deadline in the record |
| `cited` | An existing record made before 2026-10-25 | A record in `evals/` (pre-2026-10-25) or a research note on `main` |
| `screen` | A few targeted runs or one observation | A research note, or a PR note or commit message cited by name |
| `conjecture` | No run behind it | Reasoning, design, unit tests only |

2026-10-30: under the lesson contract, `reference-run` also covers a
preregistered **lesson check**: before and after on the lesson's own
challenge, on the course's reference host, with the record under
`evals/<date>-<lesson>-check/` and its preregistration in
`docs/superpowers/research/`.

On the site each badge shows as a coloured pill with an icon, so you can read a
step's strength at a glance: a green check for `reference-run`, a blue book for
`cited`, an amber flask for `screen` and a grey question mark for `conjecture`.
Each pill links back to this table.

For steps 1, 2, and 4 the badge is the strongest evidence the statement rests on. For steps 3 and 5 it is the strength of the evidence itself.

## Why the backend matters

All measured evidence in this repo was originally run on oMLX (Apple Silicon). Once a lesson gets a llama.cpp `reference-run`, its badge will say so. Until then, a `cited` badge means the number came from oMLX or mlx-lm; your llama.cpp numbers may differ, and llama.cpp itself is smoke-tested only so far ([backend](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/backends/llamacpp.md)).

Changed 2026-10-20: the track teaches llama.cpp, not Ollama; the plan chose Ollama so a learner without Apple Silicon was covered, and that port stays a backlog option ([why](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/specs/2026-10-20-learning-center-design.md)).

## Upgrading and downgrading a badge

Each lesson whose steps 3 or 5 are below `reference-run` gets a roadmap item for the run. When the run lands, the lesson's badge, numbers, and Interpretation change in the same commit as the record, with a dated line under the Interpretation saying what changed. A run that weakens a claim downgrades the badge the same way. A badge never changes without a linked record.

## Why a screen is a lead, not a rate

The project follows the rule: [evals are screens first, preregistered runs to decide](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/sdd.md). A `screen` badge means someone ran a few targeted tests and saw something worth pursuing. It is not a rate you can trust; it is a lead. Fix the arms, sample size, scoring, and the rule before runs that decide a change or claim.
