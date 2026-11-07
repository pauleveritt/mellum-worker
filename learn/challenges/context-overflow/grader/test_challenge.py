"""The context-overflow lesson's challenge, hidden grader. Eight long notes, about 80,000 tokens
together, each naming its owner only at its end: reading them all whole overruns a 64k window,
and Pi compacts the context, losing detail (record.json caps compactions at 0)."""

from pathlib import Path

OWNERS = {"Aurora": "Thandi Mokoena", "Basalt": "Rui Fernandes", "Cinder": "Amara Okafor",
          "Dune": "Lena Fischer", "Ember": "Kenji Watanabe", "Fjord": "Ingrid Larsen",
          "Granite": "Priya Raman", "Harbor": "Mateo Alvarez"}


def lines():
    path = Path("owners.md")
    assert path.is_file(), "owners.md was not written"
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def test_every_owner_is_right():
    found = {}
    for line in lines():
        if line.startswith("Project ") and ":" in line:
            name, owner = line[len("Project "):].split(":", 1)
            found[name.strip()] = owner.strip()
    assert found == OWNERS

