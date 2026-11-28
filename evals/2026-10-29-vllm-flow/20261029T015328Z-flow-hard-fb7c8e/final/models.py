from dataclasses import dataclass, field
from datetime import datetime, timezone

_next_id = [1]
_audit_seq = 1
audit = []  # list of audit entries

@dataclass
class Complaint:
    agent_name: str
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int = field(default=0)
    status: str = "open"
    archived_at: datetime = field(default=None)

    def __post_init__(self):
        if self.id == 0:
            self.id = _next_id[0]
            _next_id[0] += 1

complaints = [
    Complaint(agent_name="Agent1", text="Scope creep never ends."),
    Complaint(agent_name="Agent2", text="Unclear instructions lead to rework."),
    Complaint(agent_name="Agent3", text="Contradictory feedback complicates development."),
    Complaint(agent_name="Agent4", text="Too many meetings reduce productivity."),
]
