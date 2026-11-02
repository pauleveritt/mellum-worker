---
title: Working With Pi
track: getting-started
position: 2
prerequisites: [getting-started/base-pi-on-llamacpp]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# Working With Pi

The last step ran Pi once, with `-p`, and exited. This one opens Pi's
interactive terminal: where you type, what the model can touch, how to see
what it did, and how to pick up a session later. It ends with the command the
whole recipe is built on — the worker's `/mellum` — and the course commands
`/remedy` and `/lesson` that build on it.

Everything here is from Pi's own documentation for the version this repo
pins (1.4.0). The `/` menu inside Pi is the exact list for your session.

![A small robot in a chair typing at a keyboard in front of a large monitor, with two folders and a wrench on the floor beside it](../assets/illustrations/working-with-pi.webp){ .illustration }

## 1. Start Pi in a project folder

Pi works on the folder you start it in. It uses that folder to find files,
instructions and configuration, and to group saved sessions. Start the
model server, point Pi at the course profile as in the last step, and start
Pi from the repository root:

```bash
uv run scripts/backend.py start
export PI_CODING_AGENT_DIR=$PWD/learn/code/profile
pi --provider llamacpp --model Mellum2.1-12B-A2.5B-Thinking
```

(On Windows, set `PI_CODING_AGENT_DIR` the way the last step did for your
shell.) The screen has three parts: the conversation, an editor where you
type, and a footer with the folder, model, session and context usage.

To quit, type `/quit`, or press `Ctrl+D` while the editor is empty.
`Ctrl+C` clears the editor; pressing it a second time exits.

## 2. Type a prompt

Type a request and press `Enter` to send it. `Shift+Enter` adds a line, and
`Ctrl+G` opens your external editor for a longer prompt. Type `@` to search
for a file and add it to the prompt, and `Tab` to complete a path.

You can keep typing while Pi works. `Enter` steers the current task after
the running response and its tool calls finish; `Alt+Enter` queues a
follow-up for after the task. `Escape` stops the current task.

## 3. The tools, and seeing what Pi did

A tool is something the model can call instead of only replying. Pi's
built-in tools are:

| Tool | What it does |
| --- | --- |
| `read` | Read a text file or a supported image |
| `write` | Create or overwrite a file |
| `edit` | Apply an exact text replacement to an existing file |
| `bash` | Run a shell command |
| `ls` | List a directory |
| `find` | Find paths by glob pattern |
| `grep` | Search file contents |

By default Pi offers the model `read`, `bash`, `edit` and `write`; `--tools`
or the `defaultTools` setting changes the set. Pi does not ask before each
tool call, so it can change and run anything your user account can. Work in
a checkout you can reset, and review what it changed.

To see what happened:

- The conversation shows every tool call and its result. `Ctrl+O` expands or
  collapses tool output; `Ctrl+T` shows or hides thinking.
- `!git status` runs a command and adds its output to the conversation;
  `!!git diff` runs it without sending the output to the model.
- `/session` shows the session file, its ID, the message count, token usage
  and cost. `/export` writes the session as HTML or JSONL.

## 4. Sessions

Pi saves each session automatically, unless it was started with
`--no-session`. With the course profile, they are kept under
`learn/code/profile/sessions/`.

| To | Do |
| --- | --- |
| Resume the most recent session in this folder | `pi --continue` (or `-c`) |
| Pick a saved session | `pi --resume` (or `-r`), or `/resume` inside Pi |
| Start a fresh one | `/new` |
| Name the current one | `/name <name>` |

A session is a tree, so going back does not erase work. `/tree` moves to an
earlier point in the same session; selecting one of your messages puts its
text back in the editor to edit and resend. `/fork` starts a new session from
an earlier message, and `/clone` copies the current branch into a new
session. `/compact` shortens the history sent to the model; the saved
entries are kept.

## 5. The slash commands that matter

Type `/` to list every command in your session, with the ones extensions
add. The ones this course uses:

| Command | What it does |
| --- | --- |
| `/model` (or `Ctrl+L`) | Select a model |
| `/thinking` (or `Shift+Tab` to cycle) | Set how much the model reasons |
| `/settings` | Change common preferences |
| `/hotkeys` | Show the active keyboard shortcuts |
| `/reload` | Reload extensions, skills, templates, themes and context files |
| `/trust` | Save a project trust decision for future Pi processes |
| `/quit` | Quit Pi |

### Project trust

A project can carry its own Pi resources in `.pi/`, and an extension there is
code that runs inside Pi. So Pi loads `.pi/extensions` (and project settings,
skills and prompts) only after you grant the folder project trust. When it finds them, it
asks at startup; `/trust` saves the decision for later Pi processes, in the
agent directory (`learn/code/profile/trust.json` with the course profile).
A trust decision does not affect the session already running, so after
`/trust`, quit and start Pi again.

Context files such as `AGENTS.md` load whether or not you trust the folder.
Trust is not a sandbox either: it decides what loads, not what a tool call
can reach.

## 6. The worker: `/mellum`

The worker is the core — everything in this course builds on it. `/mellum`
comes from the installed `mellum-worker` package (the `pi install` line from the
README, the same recipe this course teaches), so it is there in any project
where you install it, not only this checkout. With it you hand bounded work to
the small local model and read how each run went.

| Command | What it does |
| --- | --- |
| `/mellum on` | Switch the session to Mellum — model, the worker tool set, the worker prompt — and stay on across turns; it marks the span start |
| `/mellum off` | Restore the model and tools you had before, and print a one-line summary of the span |
| `/mellum <task>` | One-shot: switch to Mellum, run the one task, and switch back when it settles; your model gets one handoff block for the span |
| `/mellum check` | Compare the model server and Pi's provider entry with the measured settings; it fails on a per-request mismatch and only reads |
| `/mellum last` | The newest run at or under this directory (Mode or one-shot) as a table, with no model call |
| `/mellum learn [n]` | Read the last `n` runs (default 10), name what went wrong, and suggest the `## Mellum` lines your `AGENTS.md` lacks |

`check`, `last` and `learn` also have terminal forms
(`node scripts/mellum.mjs …`).

## 7. The course commands, built on the worker: `/remedy` and `/lesson`

This repository's `.pi/extensions/` loads two more commands, so they appear only
after you trust the checkout and restart Pi. Both build on the worker: `/remedy`
switches the worker's fixes on and off, and `/lesson` teaches each one.

### `/remedy`: switch remedy units on and off

A remedy unit is one fix for one failure, in one file. `/remedy` installs every
unit at session start, and all of them start off, so the session is plain Pi
until you switch something on.

| Command | What it does |
| --- | --- |
| `/remedy` | A picker of every unit, marked on (`●`) or off (`○`); pick one to flip it |
| `/remedy on guard/break-repeat-loops` | Switch one unit on |
| `/remedy off guard/break-repeat-loops` | Switch it off |
| `/remedy preset:easy` | Switch on every unit in a preset |

A switch takes effect at the next tool call or model request. While any unit
is on, the footer shows `remedies: N on`. A unit that adds a tool registers it
the first time it is switched on; Pi cannot remove a tool, so the tool stays
offered after `off` until you restart Pi (its hooks do stop).

### `/lesson`: the course inside Pi

`/start` opens your next lesson, and on the first run of a fresh checkout it
offers a pick-a-mode menu — **Standard** (code with Mellum, every remediation
on), **Lesson** (the course), or **Challenge** (the graded run).

`/lesson` opens a lesson hands-on: it moves Pi into the lesson's `project/<id>/`
folder with a panel pinned above the prompt — the lesson, step by step, and its
run results — while the prompt below stays yours. Page the panel with `←`/`→`
(while the prompt is empty), and run the lesson's arms with `/lesson before` and
`/lesson after`. `/lesson` with no argument picks a lesson, `/lesson S0` opens
one directly, `/lesson read` shows the prose, and `/lesson back` leaves the
folder. (The findings lessons are being rebuilt — see
[Lessons](../lessons/index.md).)

## What you have

Pi running interactively on the local Mellum, the keys to steer and stop it,
the tools it can call, the commands to resume or branch a session, the worker's
`/mellum` — the core the recipe is built on — and the course's `/remedy` and
`/lesson` loaded from a trusted checkout. Next,
[Eval suites and the telemetry](eval-suites.md) runs whole projects through the
provided harness and grades them.
