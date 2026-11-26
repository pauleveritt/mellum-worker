"""cut_mix: cut a raw pair set to a fixed mix of phase, step and pathology pairs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cut_mix import cut  # noqa: E402


def row(phase, win, lose):
    return {"phase": phase, "src": [win, lose]}


def test_phase_pairs_round_robin_over_distinct_losers():
    rows = [row("medium:p2", f"w{i}", "L1") for i in range(10)] + [row("medium:p2", "w0", "L2"), row("medium:p2", "w1", "L3")]
    got = cut(rows, per_phase=3, phases=["medium:p2"], steps=0)
    assert sorted(r["src"][1] for r in got) == ["L1", "L2", "L3"]  # one per loser before any loser repeats


def test_steps_are_sampled_and_pathologies_all_kept():
    rows = ([row("medium:p2:step", "s", f"s{i}") for i in range(10)] + [row("medium:p3:outside", "o", "o")]
            + [row("medium:p4:unused", "u", "u")] + [row("py3.15-x:p1:idiom", "i", "i")] + [row("hard:p2", "w", "l")])
    got = cut(rows, per_phase=5, phases=["medium:p2"], steps=4)
    kinds = sorted(r["phase"].rsplit(":", 1)[-1] for r in got)
    assert kinds == ["idiom", "outside", "step", "step", "step", "step", "unused"]  # hard:p2 is not a listed phase


def test_cut_is_deterministic():
    rows = [row("medium:p2:step", "s", f"s{i}") for i in range(50)]
    assert cut(rows, steps=10, phases=[]) == cut(rows, steps=10, phases=[])


def test_training_task_phase_pairs_are_kept_up_to_the_cap():
    rows = [row("py3.15-sentinel-unset:p1", f"w{i}", f"l{i}") for i in range(30)] + [row("satyrn-x:p1", "w", "l")]
    got = cut(rows, per_phase=20, phases=[], steps=0)
    assert len(got) == 20 and all(r["phase"].startswith("py3.") for r in got)
