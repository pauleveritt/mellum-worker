from dataclasses import dataclass, field
from datetime import datetime, timezone

_id_counter = 0

def _next_id():
    global _id_counter
    _id_counter += 1
    return _id_counter

@dataclass
class Complaint:
    agent_name: str
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int = field(default_factory=_next_id)
    status: str = field(default="open")

complaints: list[Complaint] = [
    Complaint(agent_name="Alice", text="Unclear instructions on the main page."),
    Complaint(agent_name="Bob", text="Contradictory feedback from different modules."),
    Complaint(agent_name="Charlie", text="Scope creep never ends."),
    Complaint(agent_name="Dana", text="Feature request for better filtering."),
    Complaint(agent_name="Eve", text="UI lags when there are many complaints."),
]