from dataclasses import dataclass, field
from datetime import datetime, timezone

_complaint_id_counter = 0

def _next_complaint_id():
    global _complaint_id_counter
    _complaint_id_counter += 1
    return _complaint_id_counter

@dataclass
class Complaint:
    agent_name: str
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int = field(default_factory=_next_complaint_id)
    status: str = "open"
    archived_at: datetime | None = None

complaints: list[Complaint] = [
    Complaint(agent_name="AgentA", text="Vague initial requirements led to rework."),
    Complaint(agent_name="AgentB", text="Contradictory feedback caused confusion."),
    Complaint(agent_name="AgentC", text="Scope creep never ends."),
]

audit: list = []
audit_seq: int = 0