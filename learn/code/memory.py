#!/usr/bin/env python3
"""Portable agent memory: general lessons distilled from the agent's own gate failures.

Almost a skill, but learned. A hand-written skill is portable, general procedural grounding an
author curated up front; this memory is the SAME shape grown from mistakes. The free arm
(`flow_run.py --flow-mode free`) records, per phase, the gate-failure text and whether the agent
eventually solved it. A lesson distilled from that fail -> fix is stored as a general
`{situation, lesson}` row in a portable `memory.jsonl`. Before a build the harness retrieves the
few lessons whose situation matches this phase and injects them as grounding — exactly how a skill
would ground the agent, only the rows were learned. The file travels to another machine, seeds a
fine-tune, or ships beside a smaller model for grounding.

THE ONE RULE — stay agnostic. A lesson is GENERAL discipline:

    "inspect the real columns before reading a store; never invent a column name"

NEVER the suite's answers:

    "the visits table has a date column"   <-  this is the hidden grader's answer

`agnostic_ok` rejects the obvious answer-leaks — a concrete route path, a quoted literal, or a
multi-digit expected value — because without that guard "memory" is just a cache of the oracle's
answers and every pass after it is meaningless. The guard is a BACKSTOP, not a proof: the distiller
must generalise, and a human reviews `memory.jsonl` before it ships. Zero dependencies by design —
this must run beside a small model on another machine.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Lesson:
    situation: str  # when this applies — the general shape of the task/failure, for retrieval
    lesson: str     # the general discipline to apply — never a suite-specific answer


# The agnostic guard. Each rule names a kind of answer-leak; a lesson that matches ANY is rejected.
# Kept deliberately conservative and general — it encodes NO suite-specific token itself.
_LEAK_RULES: list[tuple[str, str]] = [
    (r"/[A-Za-z][\w/-]*", "a concrete route path (say 'the route', not the literal path)"),
    (r"[\"'][^\"']+[\"']", "a quoted literal value (describe the requirement, don't quote the answer)"),
    (r"\d{2,}", "a multi-digit expected value (assert 'the exact value the spec gives', not the number)"),
]


def leak_reason(text: str) -> str | None:
    """Why this text is NOT agnostic — the first answer-leak it carries — or None if it is clean."""
    for pat, why in _LEAK_RULES:
        if re.search(pat, text):
            return why
    return None


def agnostic_ok(text: str) -> bool:
    """True when `text` carries no obvious suite answer-leak. Necessary, not sufficient (see module
    docstring): a human still reviews the memory before it grounds a run or ships with a model."""
    return leak_reason(text) is None


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 2}


class Memory:
    """A portable store of general lessons, backed by an append-only JSONL file. Reads survive a
    move to another machine; writes are guarded and deduped. Retrieval ranks by token overlap of
    the `situation` — zero-dep, so it runs anywhere the small model does."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.lessons: list[Lesson] = []
        self.load()

    def load(self) -> None:
        self.lessons = []
        if not self.path.exists():
            return
        for line in self.path.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                self.lessons.append(Lesson(row["situation"], row["lesson"]))
            except (json.JSONDecodeError, KeyError):
                continue  # a corrupt line never sinks the store

    def add(self, situation: str, lesson: str) -> bool:
        """Store a general lesson. Rejected (returns False) if it is not agnostic, is empty, or
        duplicates one already held — so a run can call this freely on every failure."""
        situation, lesson = situation.strip(), lesson.strip()
        if not situation or not lesson:
            return False
        if not agnostic_ok(lesson):  # the lesson is what gets injected — guard it, not the situation
            return False
        if any(x.lesson == lesson for x in self.lessons):
            return False
        self.lessons.append(Lesson(situation, lesson))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fh:
            fh.write(json.dumps({"situation": situation, "lesson": lesson}) + "\n")
        return True

    def retrieve(self, situation: str, k: int = 3) -> list[Lesson]:
        """The k lessons whose situation best overlaps `situation`. Only positive overlaps — an
        unrelated phase gets no grounding rather than noise. Stable: ties keep insertion order."""
        q = _tokens(situation)
        if not q:
            return []
        scored = []
        for i, x in enumerate(self.lessons):
            overlap = len(q & _tokens(x.situation))
            if overlap:
                scored.append((overlap, -i, x))
        scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
        return [x for _, _, x in scored[:k]]

    def as_grounding(self, lessons: list[Lesson]) -> str:
        """Format retrieved lessons for injection into the coder prompt — '' when there are none,
        so the caller injects nothing rather than an empty heading."""
        if not lessons:
            return ""
        body = "\n".join(f"- {x.lesson}" for x in lessons)
        return ("LESSONS FROM EARLIER WORK (general discipline — apply where relevant; they contain "
                "no answer, so still read the real spec and data):\n" + body)


# A small, built-in distiller: it maps a FAILURE SIGNATURE (general, read off a pytest/traceback)
# to GENERAL discipline. The keys are failure-shaped, the values are suite-agnostic habits — the
# same knowledge a skill or the examiner prompt already carries, here made learnable and portable.
# A model-backed distiller would replace this; the rules make the mechanism testable without one,
# and every value is written to pass `agnostic_ok`.
_DISTILL_RULES: list[tuple[str, str, str]] = [
    (r"no such column|has no column|unknown column|KeyError",
     "reading a store whose columns you assumed",
     "inspect the real columns before you read a store (PRAGMA table_info / a SELECT) and use the "
     "columns that exist; never invent one or assume a name the data does not use"),
    (r"follow_redirects|3\d\dx|is a redirect|assert 3|== 3\d\d",
     "asserting a redirect status from the test client",
     "build the test client with redirect-following disabled so a 3xx assertion sees the redirect "
     "itself, not the followed page"),
    (r"assert \d+ ==|== \d+\b.*count|absolute total|expected \d+ (rows|items)",
     "asserting an absolute total against a shared store",
     "capture the count or total before your change and assert the delta, not an absolute total — "
     "tests share a store other tests have already mutated"),
    (r"IntegrityError|UNIQUE constraint|duplicate",
     "a write that collided with existing data",
     "do not assume a seed record exists at a fixed id or in a clean state; create the records a "
     "test needs, and roll back any row you add to a persistent store"),
    (r"TemplateNotFound|jinja|NameError: .*template",
     "a view that renders a template",
     "render through the app's existing template conventions; confirm the template exists before "
     "referencing it rather than guessing a name"),
]


def distill(failure_text: str) -> Lesson | None:
    """Turn a gate FAILURE into one general, agnostic lesson, or None if nothing general is learned.
    Matches a failure signature, not suite content, so the lesson transfers to any suite."""
    for pat, situation, lesson in _DISTILL_RULES:
        if re.search(pat, failure_text, re.IGNORECASE):
            return Lesson(situation, lesson) if agnostic_ok(lesson) else None
    return None
