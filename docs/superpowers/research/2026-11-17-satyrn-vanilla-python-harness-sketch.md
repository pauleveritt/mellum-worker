# A Satyrn harness in plain Python: a sketch for Paul (2026-11-17)

Paul, this is a one-file sketch of what a new Satyrn harness could look like if we wrote it ourselves in plain Python:
the standard library only, no framework, no agent library. It pulls together what three projects taught us:

- **mellum-worker**: Pi plus explicit remedies, the acceptance gate, and your handover proposals.
- **tern**: my small-model harness, with its own loop, checks on every turn, concepts and a ledger.
- **satyrn-evals**: your eval rules. Preserve before judging, verdicts from an oracle, freeze before spending.

I've also read Hermes Agent and DeepSeek Harness from source, and added the few things where both converged.

## What is measured / what is conjecture

**Measured on Mellum 2.1 (12B-A2.5B, Q4).** Every row is a screen, so every one is a lead, not a rate.

| What | Result | Where |
|---|---|---|
| mellum-worker, one pass, no gate, Medium | 18/18 on 2 of 4 runs | one-pass vs architect note, 2026-11-08 |
| one pass vs the architect/plan loop | about 5× fewer requests at an equal or better score | the same note |
| one pass + frozen acceptance gate, messages say wanted + found | 18/18 on 3 of 3, mean 42 requests | reply to handover, 2026-11-15 |
| the same units as `preset:medium` | 18/18 on 2 of 3, mean 73 requests | reply to handover, 2026-11-17 |
| the gate's messages | 2 of 3 green with reasons; 0 of 3 with what was found; 3 of 3 with wanted + found | reply to handover |
| a foreground-server hang, Easy | prose rules 2 of 3 stalled; a guard or a background rewrite 0 of 3 | enforce vs prose note, 2026-11-03 |
| the baseline preset, Easy | 7 of 9 (one doctype miss, one `tail -f` hang); with no-live-server added, 3 of 3 | reply to handover, 2026-11-16 |
| tern, test gate + medium thinking, mellum-easy | 9 of 10 | tern `evals/builds/RESULTS.md` |
| tern on mellum-medium | 0 of 4 (medium thinking); 1 of 3 (thinking on); 1 of 5 (low) | the same |

One caution about the tern rows: tern passes a run when it ends done AND its judge passes, while mellum-worker scores
the hidden grader out of 18. The two aren't directly comparable.

**Read from source, not run:** Hermes Agent v0.23.1 and DeepSeek Harness 0.2.2-rc.1.

**Conjecture:** the design below. None of it exists yet.

## The one thing to take from the numbers

tern grew dozens of checks, each telling the model about one particular mistake at its line. Each check helped in its
own case, but Medium stayed at 0 to 1 of 3 to 5. mellum-worker kept a thin worker and added one generic guarantee:

- a frozen acceptance test that the agent can't see or change;
- re-run when the agent tries to finish;
- its failures handed back saying what was wanted and what was found.

That took Medium from a coin flip to 18/18 on 5 of 6 runs over two screens, the clearest result we have. So the
harness is built around that gate, and everything else is a small, switchable remedy that has to earn its place.

## Principles (each one traced to where it came from)

1. **The model is fixed; every gap is the harness's job.** Never "the model can't". *(mellum-worker)*
2. **Done is a test result, never the model's word.**
   - The acceptance test is external, complete and unweakenable.
   - It's proven in both directions before any model run: green on a reference build, red on a known miss.
   *(mellum-worker, tern ADR-0022, satyrn-evals invariant 5)*
3. **A failure says what was wanted and what was found**, in that order. *(mellum-worker, measured)*
4. **One pass, not a plan loop.** One agent builds the whole task. Planning is a remedy to be measured, not the default.
   *(mellum-worker: about 5× fewer requests; tern ran its Mellum screens with plan-first off)*
5. **A rule that matters is code, not prose.** Prose is the explanation, and enforcement does the work.
   *(mellum-worker, measured on the hang)*
6. **The floor is a plain loop.** Every behaviour beyond it is an explicit remedy unit, switchable, with its evidence
   written on it. Presets nest on a tested base. *(mellum-worker's thin-worker architecture)*
7. **Few tools.** A small model does better with eight tools than forty. *(tern ADR-0017)*
8. **Keep time bounded, without names.** A command that outlives its timeout becomes a background job, never a hang.
   *(Hermes and DeepSeek Harness; our `tail -f` hang)*
9. **Record everything, and preserve before judging.** The model request as sent, every tool input and output, every
   remedy decision. Grade only what's retained. *(tern ADR-0013, satyrn-evals invariants 1 and 2)*
10. **The stable prompt goes first.** System text and tools sit before the cache boundary; anything that changes per
    turn goes after it. *(mellum-worker, prompt cache layering)*
11. **Cost is counted in requests and turns, not wall time.** Wall time is informational; a hang guard is loose, and
    an unfinished run is censored, not timed. *(mellum-worker)*

## The shape: one package, about ten files

```
satyrn_harness/
  __main__.py      CLI: run, replay, screen
  model.py         OpenAI-compatible client over http.client: stream, usage, stop sequences
  loop.py          the turn loop: request → reply → tool calls → results → settle
  tools.py         read_file, write_file, edit_file, run, process, list, find, final_answer
  shell.py         subprocess runner: timeout → job, pager-free env, output head+tail with a spill file
  hooks.py         the five hook points remedies attach to
  remedies/        one file per unit; presets as JSON lists
  gate.py          the acceptance gate: run the frozen test, parse failures, build the hand-back
  record.py        append-only JSONL per run + a SQLite index; secrets redacted on write
  screen.py        n reps, per-rep requests / turns / wall / score, preregistered rule
```

Only the standard library: `http.client`, `json`, `subprocess`, `sqlite3`, `pathlib`, `hashlib`, `difflib`,
`argparse`, `time`, `signal`. The project under test brings its own test runner. The harness only runs it.

## The loop

```python
def run(task, workspace, profile, remedies, gate):
    rec = Recorder(workspace)                    # every call below goes through it
    msgs = [system_prompt(profile, remedies),    # stable: cached first
            user(task)]
    for turn in range(profile.max_turns):
        hooks.fire("before_request", msgs)       # remedies may append (after the cache boundary)
        reply = model.chat(msgs, tools=TOOLS, profile=profile)        # recorded
        msgs.append(reply)
        if not reply.tool_calls:
            if (more := hooks.before_settle(reply)) is None:          # the gate is a before_settle remedy
                break                                                 # truly done
            msgs.append(user(more))                                   # hand back, go again
            continue
        for call in reply.tool_calls:
            verdict = hooks.tool_call(call)                           # block / rewrite / allow
            result = verdict.blocked or tools.run(call, workspace)    # recorded
            result = hooks.tool_result(call, result)                  # e.g. "unchanged since your last read"
            msgs.append(tool_msg(call, result))
        hooks.fire("turn_end", reply)
    return rec.finish()
```

That's the whole core. Everything interesting is a remedy on one of the five hooks:

- `before_request`
- `tool_call`
- `tool_result`
- `turn_end`
- `before_settle`

These are the same points Pi gives extensions, so every mellum-worker unit ports almost line for line.

## A remedy unit

```python
# remedies/guard_live_server.py
META = {
    "pathology": "debugs HTTP by starting a live server and curling it; the forked server disagrees with the in-process client",
    "does": "blocks any server start or loopback probe; points at the in-process test client",
    "model_sees": "That starts a server... exercise the endpoint in process: TestClient(app).get(...)",
    "cost": {"tokens_per_turn": 0, "breaks_cache": False},
    "evidence": "2 of 3 gated Medium reps stalled in this spiral without it; Easy 3/3 with it (guard never fired)",
}

def install(h):
    @h.on("tool_call")
    def block(call):
        if call.name == "run" and is_server_start(call.args["cmd"]):
            return Block(META["model_sees"])
```

Every unit carries:

- `pathology`: the failure it's for;
- `model_sees`: the exact text it adds;
- `cost`;
- `evidence`: a screen, or "unmeasured".

A preset is a JSON list; `baseline` is the units that passed Easy, and each harder tier adds only what its own
measured run loaded. `--remedy off:<unit>` reproduces any older result.

## The gate (the part that moved the numbers)

```python
def before_settle(reply, state):
    result = run_tests(ACCEPTANCE_TEST, cwd=workspace, pythonpath=workspace, timeout=120)
    if result.passed:
        return None                                      # done, for real
    if state.rounds >= MAX_ROUNDS:                       # 5 in mellum-worker
        return None                                      # stop; the record says the gate stayed red
    state.rounds += 1
    failing = result.failures                            # [(test_name, wanted, found)]
    if failing == state.last_failing:                    # same miss again: change the brief, don't repeat it
        return brief_for_repeat(failing, workspace)      # name the contract and the line that breaks it
    state.last_failing = failing
    return "These checks still fail:\n" + "\n".join(f"- {n}: wanted {w}; found {f}" for n, w, f in failing)
```

What makes it work:

- **The acceptance test lives outside the workspace,** so the agent never sees or edits it. It's written once from
  the spec.
- **It's a superset of the hidden oracle,** and its every assertion says wanted and found.
- **It's proven before any model run:** green on a complete reference build, red on a build with the known miss.
- **The repeat rule is new and unmeasured.** One `preset:medium` rep held the same miss through all five rounds. The
  messages were right, and resending them bought nothing.

## The shell (where small models hang)

- **Promote, don't kill.**
  - Every command gets a wall-clock timeout: 120 s by default, 600 s at most.
  - Past that, it isn't killed. It keeps running as a job, and the call returns
    `still running after 120s; moved to job 3` plus the output so far.
  - `process logs/wait/stop 3` handles it from there.
  - That's what Hermes and DeepSeek both do. Pi's timeout is optional and resets on any output, so a `tail -f` on a
    busy log never ends.
- **Pager-free environment.** Every command runs with `PAGER=cat GIT_PAGER=cat NO_COLOR=1 TERM=dumb`.
- **Bounded output.** Head and tail kept, the middle in a spill file whose path is in the result. A file read is never
  spilled, or the agent loops reading the spill.
- **Servers.** Whether to manage them as jobs with a readiness line, or ban them outright, is the first A/B to screen.
  The ban is what's measured.

## Tools (eight, and no more to start)

| Tool | Notes |
|---|---|
| `read_file` | a re-read of an unchanged region returns "unchanged since your last read" (Hermes) |
| `write_file` | refused on an existing file not read since it changed (Hermes, DeepSeek) |
| `edit_file {path, old, new}` | one unique match, tolerant of whitespace and indentation drift (Hermes) |
| `run` | the shell above |
| `process` | `logs`, `wait`, `stop` for jobs |
| `list`, `find` | workspace-confined |
| `final_answer` | ends the turn; the gate decides whether the run ends |

## Loop safety (generic, never keyed to a suite)

- **Repeats.**
  - A repeat counts only when the tool, the arguments AND the result are all the same.
  - Cycles of period 2 to 4 count too.
  - Advise on the 3rd, block on the 5th. *(Hermes; mellum-worker blocks at 5 on tool and arguments only)*
- **Empty turns.** An empty reply after tool calls gets one nudge, then one retry with thinking off, then a stop.
- **Thinking.** It's short by default: a budget for planning calls, none for acting calls. *(tern ADR-0023)*
  mellum-worker measured that reduced thinking lets a turn cap fit on Medium.
- **Turn caps are per tier.** A cap that bounds Easy starves Medium. *(mellum-worker, measured)*
- **No coding to the eval.** A remedy carries no route, column, count or expected string from a suite. A generic
  developer token (`app.py`, a launcher name) is fine.

## The record (your invariants, made concrete)

- **What each run writes:** `run.jsonl`, one event per line.
  - each request as sent and each reply, with usage;
  - each tool call, result and file diff;
  - each remedy decision and gate round.
- **The index:** `index.sqlite` holds one row per run, pointing at its log. The log is the truth.
- **Preserve, then grade.** The workspace, patch and transcript are saved before the oracle runs. The verdict comes
  from the oracle's own result, never from stdout.
- **Freeze before spending.** A screen records the model as served, the settings (verified against the server, not
  declared), the remedy list with hashes, the acceptance test hash, n and the rule, all before the first rep runs.
- **Per-rep reporting:** score, requests, turns, wall, gate rounds, stop reason. A pass that took fewer requests is a
  better pass.

## Build order

1. `model.py`, `loop.py`, `tools.py`, `shell.py`, `record.py`. A plain loop that runs Easy. Report its score as the
   floor.
2. Port the baseline units to hooks: name-the-layout, python-developer, foreground-server, verify-the-spec,
   no-live-server. Screen Easy at n=3 against mellum-worker's 3 of 3.
3. `gate.py` with the existing frozen `test_medium.py`. Screen Medium at n=3 against Pi + `preset:medium`. Same model,
   same server, same test.
4. The shell's timeout-to-job, read stubs, result-keyed repeats. One unit per screen, each on the tier it targets.
5. Only then: concepts one at a time (tern ADR-0022) and planning, each against the plain one-pass loop.

The parity rule, borrowed from tern ADR-0008: the plain-Python harness must match or beat Pi + remedies on every
screened tier before it replaces it. Until then, Pi stays the measured product.

## Why plain Python and not Pi

- **The pros.**
  - It's one language for the harness, the remedies, the gate and the evals.
  - There's no extension seam to work around. Pi's last-handler-wins `agent_before_settle` cost us a bug fix.
  - The request the model actually gets is ours to record.
- **The cons.**
  - Pi is measured and ours isn't.
  - Pi brings session handling, compaction and providers for free.
- **The cost of finding out** is steps 1 to 3 above, a few days' work. The answer is the Easy and Medium screens, not
  this sketch.

## What would falsify this / risks

- **The core bet is wrong** if a plain loop plus the ported units can't match Pi + the same units on Easy at n=3: the
  harness would be the cost, not the remedies.
- **The gate claim is wrong** if it doesn't lift Medium over the same loop with no gate, at n fixed in advance. It
  rests on 5 of 6 at n=3 per screen today.
- **tern's lesson cuts both ways.** Its per-mistake checks didn't crack Medium on Mellum, but its scoring differs from
  ours. A fair read needs the same suite, grader and model under both harnesses.
- **Borrowed thresholds are guesses for this model:** the 120 s timeout, repeats at 3 and 5, five gate rounds. Each
  is a setting to screen, not a fact.
