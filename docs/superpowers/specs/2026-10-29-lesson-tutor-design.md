# The lesson tutor: `/lesson` inside Pi

Date: 2026-10-29. Status: approved by Andre on 2026-10-29.

## Intent

Pi is the harness the course teaches, so the course should run inside it. A
learner who opens Pi in a checkout of this repository types `/lesson`, picks a
lesson, and is taken through it: the picture, the problem, the *before* run
and its FAIL, what the record shows, the remedy, the *after* run and its PASS,
and the key points, then on to the next lesson. Reading the site is optional.

## Decisions

- **The lesson page is the only source.** The tutor parses
  `learn/lessons/<tier>/<slug>.md`: front matter, the opening, the picture and
  its alt text, the Overview, Paul's six steps, the Run it yourself commands
  and the key points. Nothing is written twice; the site and the tutor cannot
  disagree.
- **Loaded per project.** `.pi/extensions/lessons.ts` loads the tutor when Pi
  runs in this repository (after project trust). It is not added to the
  installed package: the lessons need the repository's harness and suites.
- **No model in the tutor.** Navigation, runs and summaries are deterministic.
  The Pi session's own model stays free for the learner's questions.
- **Runs are real.** The tutor runs the page's own before and after commands
  through `learn/code/harness.py`, into a fresh runs folder, and summarises
  each session's `run.json`: PASS or FAIL, whether the checks ran, what
  stalled, how long. By default it runs one session per arm and says so (a
  demonstration, not the lesson check); `R` runs the page's own n.
- **Pictures in the terminal.** Pi's `Image` component draws the lesson's
  picture on terminals that support the Kitty or iTerm2 protocol, and its alt
  text elsewhere. Kitty takes PNG only, so each illustration gets a small PNG
  copy under `learn/assets/illustrations/terminal/`.
- **Progress** is a small JSON file in the agent directory, so `/lesson`
  marks finished lessons and opens on the next one.

## The walk-through

One screen per step; `→`/`Enter` next, `←` back, `r` run (on the steps that
run), `R` run at the page's n, `Esc` leave:

1. Cover: picture, number and title, opening, questions and objectives.
2. Problem.
3. Eval case, with the **before** line; `r` runs it and shows the result.
4. Evidence of the problem.
5. Solution: the remedy unit, its code, the **after** line; `r` runs it.
6. Validation and Interpretation.
7. Key points, and the next lesson.

## Remedies, switched on by hand

Working by hand, the learner turns a remedy on in the live session and sees
the difference on the next call:

- `/remedy` opens a picker of every unit with its pathology, marked on or off.
- `/remedy on <kind/name>`, `/remedy off <kind/name>` and
  `/remedy preset:<name>` toggle units, with completion on the names.
- A status line shows how many are on.

One host extension (also loaded from `.pi/extensions/`) installs every unit
at session start, each behind its own switch, so a toggle takes effect at the
next tool call or request with no restart. All start off: the session is bare
Pi until the learner turns something on. The tutor's *after* step can say
"turn it on here with `/remedy on …`" as well as run the after line.

## Out of scope

Editing lessons from the tutor; grading the learner; a model-written
explanation of a run (the summary is computed from the record).

## Acceptance

- The parser reads every lesson page into all of the above; a test runs it
  on every page.
- The run summary is computed from `run.json` and tested on recorded sessions.
- `/lesson` lists the 23 lessons in track order and walks one end to end in a
  real Pi session; a picture renders in a supported terminal.
- `/remedy on guard/break-repeat-loops` blocks the sixth identical call in a
  live session and `/remedy off` stops it; a test drives the switch.
- `npm test` and the docs caps pass.
