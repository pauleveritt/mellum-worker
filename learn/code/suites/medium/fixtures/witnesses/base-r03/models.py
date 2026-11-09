import datetime
import dataclasses

_next_id = 1

@dataclasses.dataclass
class Complaint:
    agent_name: str
    text: str
    id: int = dataclasses.field(default=None, compare=False)
    status: str = "open"
    timestamp: datetime.datetime = dataclasses.field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __post_init__(self):
        if self.id is None:
            global _next_id
            self.id = _next_id
            _next_id += 1

# Seeded complaints
complaints = [
    Complaint("Agent A", "First complaint."),
    Complaint("Agent B", "Scope creep never ends."),
    Complaint("Agent C", "Third complaint."),
    Complaint("Agent D", "Fourth complaint."),
]

# Assign ids to seeded complaints
for i, complaint in enumerate(complaints, 1):
    complaint.id = i
    # status is already "open" by default, but ensure it
    complaint.status = "open"