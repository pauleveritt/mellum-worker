# 0010: The target is tool calling, added to a model that lacks it, by a method that works on any model

- **Date:** 2026-11-28
- **Status:** Accepted (narrows 0008)

## Context

0008 sets out to prove a small model becomes powerful when fine-tuned and harnessed properly. The first thing
to prove is narrower: that good tool calling can be added to a model that has none. Building whole apps is one
way to test that, not the goal itself. DeepSeek-R1-Distill-Qwen-1.5B is the first model; the method should not
depend on it.

## Decision

- **What is measured, in order:**
  1. calls that parse: the share of turns where llama.cpp returns a structured tool call when a call is due;
  2. calls that are right: faulty calls per 100 (an edit that matched nothing, a read of a missing file, a
     malformed command, a search outside the workspace), tool choice, valid arguments;
  3. a well-known tool-calling benchmark, held out from all training: the Berkeley Function Calling
     Leaderboard (BFCL);
  4. end to end: the Easy screen (can it drive the tools to a passing build), against the untrained model.
  Medium and harder builds are later evidence for 0008, not the bar for this step.
- **Data is chosen for tool calling, not task success.** A step whose call succeeded and fits its context is a
  good example even in a run that failed its hidden tests (the teacher may simply not know an API). Steps from
  passing runs are preferred where there is a choice; failed calls are never taught.
- **Variety over volume.** Many tasks, tools and situations beat many runs of one task. Sources: teacher
  (Mellum on the lab) runs on varied training tasks in the student's harness shape, and, if needed, general
  function-calling data with many different tool schemas, distilled through the teacher.
- **Held out from all training:** the AgentClinic family (Easy, Medium, Hard and the four Satyrn AgentClinic
  tasks), the Python eval tasks, and every public benchmark (BFCL, EvalPlus, Aider).
- **Any model.** Token surgery (0005), the template, the data builder and the trainer take the model's markers,
  template and spare rows as inputs, so the same pipeline can add tool calling to another model.

## Consequences

The proof can be made with modest GPU: tool-calling quality shows up in short runs. Training tasks need to be
written for variety, since only 20 non-AgentClinic tasks exist (8 Satyrn, 12 Python training).

## Evidence

Teacher smoke run 2026-11-28 (`runs/2026-11-28-teacher-smoke`): 19 requests, 17 tool calls, 2 tool errors, task
failed on an API the teacher doesn't know; 15 successful calls usable as examples.
