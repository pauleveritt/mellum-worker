# Source inspection and design-review corrections

## What is measured / what is conjecture

**What is measured:** local source-tree inspection at
`0e4a9b6859cbe447adbca537c5738f24a862d214`, dated 2026-11-16.
No model runs were made for this correction. Source is
[`andrevanzuydam/mellum-worker`](https://github.com/andrevanzuydam/mellum-worker/tree/0e4a9b6859cbe447adbca537c5738f24a862d214).
**What is conjecture:** file counts do not measure complexity, maintainability
or whether an extension is dead; the rewrite's benefit is still unmeasured.

## Recompute in a checkout of the source revision

| Observation | Command | Result |
| --- | --- | --- |
| Top-level TypeScript files in extensions | `git ls-tree -r --name-only 0e4a9b68 extensions` filtered by `rg '^extensions/[^/]+\.ts$'` then `wc -l` | 32 |
| All TypeScript files in extensions | Same listing filtered by `rg '\.ts$'` then `wc -l` | 34 |
| Tracked files under runs | `git ls-tree -r --name-only 0e4a9b68 runs` piped to `wc -l` | 2,245 |
| Of those, inside .venv | Same listing filtered by `rg '/\.venv/'` then `wc -l` | 2,226 |
| Worker file length | `git show 0e4a9b68:extensions/mellum-worker.ts` piped to `wc -l` | 1,962 lines |
| This inspection checkout's Git-directory disk use | `du -sk .git` | 58,896 KiB at inspection time |

The first five results describe revision contents. Git-directory disk use
also depends on local objects, refs, reflogs and housekeeping: another checkout
of the same revision need not reproduce it. The original brief's "58 MB"
was an imprecise label for that local observation. No inventory supporting
"several nothing loads" was established, so that assertion is withdrawn.

## Dated corrections, 2026-11-16

The initial brief claimed a roadmap and research owners existed when the
staging directory held only BRIEF.md and README.md. This revision supplies
the roadmap, preserved rule documents, applicability mapping and linked notes.
It does not claim that any product phase or executable gate has shipped.

The initial preset rationale said no counted run credited the current units.
That categorical claim is withdrawn: the source has incremental screens,
including n=6 results, whose limits must be retained. Starting the new presets
empty is a new-repository decision, explicitly refused for the old repository.
See [remedy credit](2026-11-16-remedy-credit.md).

Rented batches are also a departure from the source reply, not an agreed source
practice. See [batch hosts](2026-11-16-batch-hosts.md). The source has multiple
llama.cpp configurations; [reference rig](2026-11-16-reference-rig.md) records
the explicit b12066 choice. The primary inherited grade is preserved under
[grading compatibility](2026-11-16-grading-compatibility.md), and eval-managed
server provisioning is excluded for these twelve phases.

The copied source rules retain their text. Their operational mappings and
scope exceptions live in [rule applicability](../../rules-applicability.md).

## What would falsify this

Different results from the revision-content commands at the full commit above
would falsify the corresponding inventory claims. Evidence of an unused module
would justify a named finding, not retroactively establish the withdrawn
blanket claim.

## Risks

Local disk use drifts. TypeScript file counts include helpers. These observations
justify inspecting repository weight; they do not prove a rewrite improves it.
