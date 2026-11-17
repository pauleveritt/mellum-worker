from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import count

_ids = count(1)


@dataclass
class Complaint:
    agent_name: str
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int = field(default_factory=lambda: next(_ids))
    status: str = "open"


complaints: list[Complaint] = [
    Complaint("Aria", "My instructions contradict each other every other message."),
    Complaint("Bolt", "Scope creep never ends."),
    Complaint("Cleo", "Nobody tells me what done looks like."),
    Complaint("Dex", "The feedback changes every time I fix the last round."),
]

audit = []
_seq = count(1)


def record(cid, action):
    audit.append({"id": cid, "action": action, "seq": next(_seq)})
