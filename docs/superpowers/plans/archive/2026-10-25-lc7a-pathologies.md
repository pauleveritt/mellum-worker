---
phase: LC
feature_cycle: LC.7A
cycle: 1
lifecycle: closed
---

# LC.7A — the Pathologies page

## Why

Eleven pathologies are named across three research notes, six lesson pages and
one hand-driven session, and there is nowhere to read them together. The ditch
links the catalogue to a **backlog anchor** as a placeholder. This cycle ships
the page, and with it the two close-time habits that keep a catalogue like it
alive instead of frozen: the glossary rule and the pathologies rule.

## Decisions taken before this plan

- **The entry shape is three lines.** A numbered **bold name**, one plain
  sentence stating the problem, then `Seen:` (a clause and a link) and
  `Answer:` (the shape that answers it, or "nothing yet"). Harvested from
  `swiftstar/docs/pathologies.md`; see the [harvest
  note](docs/superpowers/research/2026-10-27-pathologies-harvest.md).
- **Grouped by when it bites**, not alphabetically or by model: it says it is
  done and is not; it stops before the work is done; it damages the project
  while finishing; it ignores what it was told.
- **An entry needs an observation behind it**, and the page says so. Where the
  only observation is another project's, the line reads `Seen elsewhere:` and
  names it. One entry is in that state: the runaway search.
- **This is a reference, not a denominator.** The page says it once, in its
  header, and no entry carries a rate.
- **Harness faults stay on the page**, marked as harness faults: the deadline
  counted on a sleeping clock and the server the sweep never killed. ds4-engine
  keeps such entries because a "model pathology" that reproduces perfectly can
  still be the tooling.
- **Thirteen entries, not the row's eleven.** Two more have records: the project
  that stops importing (two of six sessions in LC.19's attempt 4) and the worker
  that builds the thing somewhere else (`models.py` absent, `Complaint` in
  `app.py`). The row's list is a floor.

## Non-goals

- New measurements, or an arm for any entry. Each cites what exists.
- Enabling the foreground-server guard. It stays dormant; the entry says the
  guard refuses the call and costs retries, which is what the smoke showed.
- A lesson about one pathology — that is LC.20–LC.23.
- A `remediations.md` companion. The `Answer:` line covers it at this size; the
  harvest note records the split as the escape hatch.

## Tasks

### Task 1: The harvest note

- [x] `docs/superpowers/research/2026-10-27-pathologies-harvest.md` — what was
  taken from the two existing catalogues and what was refused.

### Task 2: The page and its test

**Files:** `learn/pathologies.md`, `tests/pathologies.test.mjs`

- [ ] **Step 1: Write the test first** — four `##` section headings, thirteen
  numbered entries, every entry carrying `**Seen` and `**Answer:**`, every
  `Seen:` line containing a link, no `evals/` link, the opening paragraph
  two sentences and under 45 words, and the phrase "not a denominator".
- [ ] **Step 2: Write the page** in the three-line shape, following the harvest
  note's mapping.
- [ ] **Step 3: Run the test and the shared site test.**

### Task 3: Wire it in

**Files:** `learn/getting-started/ditch.md`, `zensical.toml`,
`tests/learn-site.test.mjs`, `learn/glossary.md`

- [ ] **Step 1: Repoint the ditch's placeholder** from the backlog anchor to
  `../pathologies.md`.
- [ ] **Step 2: Nav entry**, after the Getting started track.
- [ ] **Step 3: `PAGES`** in `tests/learn-site.test.mjs`, so the site-wide checks
  cover the new page.
- [ ] **Step 4: One glossary entry** for `pathology`.

### Task 4: The two close-time rules

**Files:** `docs/sdd.md`, `AGENTS.md`

- [ ] **Step 1: `docs/sdd.md`'s "Closing a feature cycle"** gains two bullets:
  a glossary entry for any concept the cycle introduced, and a pathologies entry
  for any failure shape the cycle's evidence showed — or nothing, if it showed
  none.
- [ ] **Step 2: `AGENTS.md`'s "Finishing a feature cycle"** paragraph gains the
  same two in one sentence.

### Task 5: Close

- [ ] **Step 1: Changelog** — one `Added` entry for the page, and a `Changed`
  entry for the two rules.
- [ ] **Step 2: LC.7A's Status cell** and `## Now`.
- [ ] **Step 3: `## Result`**, `lifecycle: closed`, archive.
- [ ] **Step 4: Verify** — `npm test`, `docs-caps`, `zensical build`; commit and
  push.

## Risks

- **A catalogue that reads as a rate.** The header says it is not, and no entry
  carries a count; the only numbers on the page are inside cited records.
- **An entry with a thin observation.** The runaway search is `Seen elsewhere`
  and says so; if it is reproduced here later, the line changes to a record.
- **Staleness.** A page like this rots silently. The two close-time rules are
  the answer, and they are conditional on evidence so neither becomes ceremony.

## Result

2026-10-25. Shipped: `learn/pathologies.md` — thirteen entries in four sections,
each a numbered bold name, one plain sentence, `Seen:` with a link, and
`Answer:` naming the shape that answers it or saying nothing does yet. Twelve
rest on records in this repository; one (the runaway search) says `Seen
elsewhere` and names Andre's digest. Two entries are harness faults, marked as
such. The ditch's placeholder link, the nav, the site test's `PAGES` list and a
glossary entry for **pathology** all follow.

The close checklist in `docs/sdd.md` gained two steps and `AGENTS.md` gained the
same sentence: a glossary entry for a concept the cycle introduced, and a
Pathologies entry for a failure shape its evidence showed — or nothing, because
an entry without an observation is a hypothesis.

`tests/pathologies.test.mjs` holds the page's invariant: four family sections,
eleven-plus entries with unique names, every entry carrying `Seen:` (with a
link) and `Answer:`, a two-sentence opening, the "reference, not a rate" rule,
and no `evals/` link. `npm test` 386/386, docs caps 4/4, build clean.

Owed: nothing. If a later cycle reproduces the runaway search, its line changes
from `Seen elsewhere` to a record.
