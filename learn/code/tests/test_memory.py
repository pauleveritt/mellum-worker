import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import memory as mem


# --- the agnostic guard: the load-bearing rule ----------------------------------------------
# A lesson is GENERAL discipline; it must never carry the suite's answers. The guard is what keeps
# "memory" from becoming a cache of the hidden grader's answers.

def test_agnostic_ok_accepts_general_discipline():
    assert mem.agnostic_ok(
        "inspect the real columns before you read a store and use the columns that exist")
    assert mem.agnostic_ok("build the test client with redirect-following disabled")
    assert mem.leak_reason("capture the count before your change and assert the delta") is None


def test_agnostic_ok_rejects_answer_leaks():
    assert not mem.agnostic_ok("call the /visits route and check the agent column")  # route path
    assert not mem.agnostic_ok('the status label must equal "Resolved"')             # quoted literal
    assert not mem.agnostic_ok("the report total should be 600 cents")               # multi-digit value
    # and the reason names the kind of leak, so a human reviewing the memory can see why
    assert "route" in mem.leak_reason("hit /archive to confirm")
    assert "literal" in mem.leak_reason('assert body contains "Triage"')
    assert "value" in mem.leak_reason("expect 42 rows")


def test_memory_add_persists_only_agnostic_lessons(tmp_path):
    m = mem.Memory(tmp_path / "memory.jsonl")
    assert m.add("reading a store", "inspect the real columns before reading; never invent one")
    assert m.add("asserting a total", "capture the total before your change and assert the delta")
    # the guard catches the obvious answer-leaks: a route path, a quoted literal, a multi-digit value
    assert not m.add("a route", "POST to /complaints to create one")           # route path
    assert not m.add("a label", 'the status must read "Resolved" exactly')     # quoted literal
    assert not m.add("a total", "the grand total is 1200 cents")               # multi-digit value
    assert len(m.lessons) == 2  # only the two agnostic lessons were kept
    # persisted to disk and reloads identically — the file is the portable artifact that ships
    reloaded = mem.Memory(tmp_path / "memory.jsonl")
    assert [x.lesson for x in reloaded.lessons] == [x.lesson for x in m.lessons]


def test_memory_add_rejects_empty_and_duplicates(tmp_path):
    m = mem.Memory(tmp_path / "memory.jsonl")
    assert not m.add("", "a lesson with no situation")
    assert not m.add("a situation", "   ")
    assert m.add("reading a store", "use the columns that actually exist")
    assert not m.add("reading a store again", "use the columns that actually exist")  # dup lesson
    assert len(m.lessons) == 1


def test_retrieve_ranks_by_situation_overlap_and_skips_unrelated(tmp_path):
    m = mem.Memory(tmp_path / "memory.jsonl")
    m.add("reading a database store for a report", "inspect the real columns before reading")
    m.add("asserting a redirect from the client", "disable redirect-following on the test client")
    m.add("a write that collided with existing data", "create the records a test needs, roll back")
    hits = m.retrieve("building a report that reads from the database store", k=2)
    assert hits and "columns" in hits[0].lesson        # the database/report lesson ranks first
    assert len(hits) <= 2
    assert m.retrieve("something about colours and fonts") == []  # no overlap -> no noise


def test_as_grounding_is_empty_without_lessons_and_carries_the_no_answer_caveat(tmp_path):
    m = mem.Memory(tmp_path / "memory.jsonl")
    assert m.as_grounding([]) == ""
    m.add("reading a store", "inspect the real columns before reading")
    text = m.as_grounding(m.retrieve("reading a store", k=1))
    assert "inspect the real columns" in text
    assert "no answer" in text.lower()  # the injected block reminds the coder it is not the answer


def test_distill_maps_a_failure_signature_to_a_general_agnostic_lesson():
    schema = mem.distill("sqlite3.OperationalError: no such column: visited_at")
    assert schema is not None and mem.agnostic_ok(schema.lesson)
    assert "columns" in schema.lesson and "invent" in schema.lesson
    redirect = mem.distill("assert 200 == 307  # follow_redirects swallowed it")
    assert redirect is not None and "redirect" in redirect.lesson
    assert mem.distill("some unrecognised failure with no general lesson") is None
    # every built-in distilled lesson is agnostic by construction
    for _pat, _sit, lesson in mem._DISTILL_RULES:
        assert mem.agnostic_ok(lesson), lesson


# --- the example the memory is FOR: grounding solves in fewer rounds -------------------------

def _rounds_to_solve(required: list[str], known: list[str]) -> int:
    """MECHANISM DEMO — not a model measurement. An agent passes once it applies every required
    lesson; lacking one, it discovers a single lesson per round. Memory that already holds the
    lessons lets it apply them on round 1. This shows grounding short-circuits discovery; the real
    uplift on the FIXED model is the preregistered with-vs-without run (see the research note)."""
    have, rounds = set(known), 0
    while not set(required) <= have:
        rounds += 1
        have.add(next(x for x in required if x not in have))  # learns one per round
    return max(rounds, 1)


def test_example_memory_solves_in_fewer_rounds_mechanism_demo(tmp_path):
    required = [
        "inspect the real columns before reading; never invent one",
        "capture the total before your change and assert the delta",
    ]
    m = mem.Memory(tmp_path / "memory.jsonl")
    m.add("reading a database store for a report", required[0])
    m.add("asserting a report total from a shared store", required[1])
    # the phase situation retrieves BOTH lessons (overlap on store/report/total)
    retrieved = [x.lesson for x in m.retrieve("a report that reads a store and totals it", k=3)]
    assert set(required) <= set(retrieved)

    without_memory = _rounds_to_solve(required, known=[])        # discovers one lesson per round
    with_memory = _rounds_to_solve(required, known=retrieved)    # already knows them, round 1
    assert with_memory == 1 and without_memory > with_memory
