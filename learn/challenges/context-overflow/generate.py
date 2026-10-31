"""Writes base/docs/ for the context-overflow challenge: 8 project design notes of about 40 KB
each (about 80,000 tokens in all, past a 64k window), each naming its owner only in its last
section. Answering needs every note's owner, so a session that reads every note whole fills the
window and loses the first notes to compaction. Deterministic: run it again, every file is the same."""

import random
from pathlib import Path

PROJECTS = [("Aurora", "Thandi Mokoena"), ("Basalt", "Rui Fernandes"), ("Cinder", "Amara Okafor"),
            ("Dune", "Lena Fischer"), ("Ember", "Kenji Watanabe"), ("Fjord", "Ingrid Larsen"),
            ("Granite", "Priya Raman"), ("Harbor", "Mateo Alvarez")]
WORDS = ("service request queue latency budget cache shard replica schema migration rollout "
         "metric alert dashboard client server token session retry backoff index storage "
         "region failover capacity throughput window batch stream handler worker pipeline").split()
rng = random.Random(4711)
docs = Path(__file__).parent / "base" / "docs"
for f in docs.glob("*.md"):
    f.unlink()
for codename, owner in PROJECTS:
    parts = [f"# Project {codename}: design notes\n"]
    for section in range(1, 76):
        parts.append(f"\n## Section {section}\n")
        for _ in range(4):
            sentence = " ".join(rng.choice(WORDS) for _ in range(rng.randint(12, 20)))
            parts.append(f"The {codename} {sentence}.")
    parts.append(f"\n\n## Owner\n\nThe owner of Project {codename} is {owner}.\n")
    (docs / f"{codename.lower()}.md").write_text("\n".join(parts))
print("wrote", sum(f.stat().st_size for f in docs.glob("*.md")), "bytes in", len(PROJECTS), "notes")
