from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class Complaint:
    agent_name: str
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

complaints: list[Complaint] = [
    Complaint(agent_name="Agent A", text="Scope creep never ends."),
    Complaint(agent_name="Agent B", text="Unclear instructions led to wrong output."),
    Complaint(agent_name="Agent C", text="Contradictory feedback confused the model."),
]