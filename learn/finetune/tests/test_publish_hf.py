"""publish_hf: the checks and model card that gate a tuned GGUF before it goes to Hugging Face."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publish_hf import compare_meta, render_card, sha256_lines  # noqa: E402

BASE = {"general.architecture": "mellum", "mellum.expert_count": 64, "mellum.block_count": 28,
        "mellum.context_length": 65536, "tokenizer.ggml.pre": "mellum2", "tokenizer.chat_template": "{{ x }}",
        "general.name": "Base", "general.file_type": 15}


def test_identical_architecture_and_template_pass():
    ours = {**BASE, "general.name": "Ours"}  # names and file details may differ
    assert compare_meta(BASE, ours) == []


def test_a_changed_chat_template_is_refused():
    problems = compare_meta(BASE, {**BASE, "tokenizer.chat_template": "{{ y }}"})
    assert problems and "chat_template" in problems[0]


def test_a_missing_or_changed_architecture_key_is_refused():
    ours = {k: v for k, v in BASE.items() if k != "mellum.expert_count"} | {"mellum.block_count": 27}
    problems = " ".join(compare_meta(BASE, ours))
    assert "mellum.expert_count" in problems and "mellum.block_count" in problems


INFO = {
    "repo": "someone/Mellum2.1-12B-A2.5B-Thinking-dpo-mix120-GGUF",
    "gguf": "ours-mix120-Q4_K_M.gguf",
    "commit": "abc1234",
    "data": "learn/finetune/data_dpo_mix120",
    "pairs": 120,
    "updates": 30,
    "heldout_margin": 0.012,
    "results": [{"screen": "Easy", "model": "base", "passed": 3, "n": 3, "faults_per_100": 9.0},
                {"screen": "Easy", "model": "ours", "passed": 3, "n": 3, "faults_per_100": 5.0}],
}


def test_card_carries_provenance_licence_and_results():
    card = render_card(INFO)
    assert card.startswith("---\n")
    assert "base_model: JetBrains/Mellum2.1-12B-A2.5B-Thinking" in card
    assert "license: apache-2.0" in card
    assert "https://github.com/andrevanzuydam/mellum-worker/tree/abc1234/learn/finetune/data_dpo_mix120" in card
    assert "| Easy | ours | 3/3 | 5.0 |" in card and "| Easy | base | 3/3 | 9.0 |" in card


def test_card_says_a_three_rep_screen_is_a_screen():
    card = render_card(INFO)
    assert "screen" in card.lower() and "not a rate" in card.lower()


def test_sha256_lines(tmp_path):
    (tmp_path / "a.gguf").write_bytes(b"abc")
    assert sha256_lines([tmp_path / "a.gguf"]) == [
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  a.gguf"]


def test_card_has_every_section_a_reader_needs():
    card = render_card({**INFO, "files": [("ours-mix120-Q4_K_M.gguf", 7_500_000_000, "f" * 64)]})
    for heading in ("## What this is", "## How to run it", "## How it was trained", "## Training data",
                    "## Evaluation", "## Limitations", "## Files", "## Reproduce", "## Licence"):
        assert heading in card, heading
    assert "llama-server" in card and "--jinja" in card  # tool calls need the template's parser
    assert "| ours-mix120-Q4_K_M.gguf | 7.5 GB | `ffffffff" in card


def test_file_layout_counts_may_differ():
    """GGUF.kv_count and friends describe the file, not the model."""
    assert compare_meta({**BASE, "GGUF.kv_count": 47}, {**BASE, "GGUF.kv_count": 45}) == []


SCREENS = {**INFO, "results": [
    {"screen": "Easy", "model": "base", "passed": 3, "n": 3, "faults_per_100": 1.5},
    {"screen": "Medium", "model": "Tsunami", "passed": 3, "n": 6, "faults_per_100": 5.3}]}


def test_results_table_has_one_row_per_screen_and_model():
    card = render_card(SCREENS)
    assert "| Screen | Model | Passed | Faulty calls per 100 |" in card
    assert "| Easy | base | 3/3 | 1.5 |" in card and "| Medium | Tsunami | 3/6 | 5.3 |" in card


def test_training_data_lists_only_the_pair_kinds_the_set_has():
    card = render_card({**SCREENS, "kinds": {"phase": 30, "step": 40, "reread": 29, "cleanup": 7}})
    assert "**Re-read pairs (29):**" in card and "**Cleanup pairs (7):**" in card
    assert "**Phase pairs (30):**" in card and "**Step pairs (40):**" in card
    assert "Idiom pairs" not in card and "Shell pairs" not in card


def test_card_names_the_model():
    card = render_card({**SCREENS, "name": "Tsunami"})
    assert "**Tsunami**" in card.split("## What this is")[0]


def test_pair_kinds_are_counted_from_the_set_files(tmp_path):
    from publish_hf import pair_kinds
    (tmp_path / "train.step.01.jsonl").write_text("{}\n{}\n")
    (tmp_path / "train.step.02.jsonl").write_text("{}\n")
    (tmp_path / "train.reread.01.jsonl").write_text("{}\n")
    (tmp_path / "valid.step.01.jsonl").write_text("{}\n")
    assert pair_kinds(tmp_path) == {"step": 3, "reread": 1}


def test_an_early_checkpoint_says_where_it_stopped():
    card = render_card({**INFO, "pairs": 262, "updates": 15, "total_updates": 66})
    assert "66 updates" in card and "checkpoint taken at update 15" in card
    assert "(15 updates)" not in card


def test_a_full_run_states_its_updates():
    assert "(30 updates)" in render_card(INFO)
