from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

@dataclass
class Complaint:
    agent_name: str
    text: str
    id: int = 0
    status: str = "open"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.id == 0 and 'next_direct_id' in globals():
            global next_direct_id
            self.id = next_direct_id
            next_direct_id += 1

class ComplaintList(List[Complaint]):
    def append(self, complaint: Complaint) -> None:
        super().append(complaint)
        # Reassign IDs sequentially starting from 1
        for i, c in enumerate(self, start=1):
            c.id = i

# Seeded complaints using the custom list
complaints = ComplaintList()
seeded = [
    Complaint("Alice", "The coffee is too hot."),
    Complaint("Bob", "The seating is uncomfortable."),
    Complaint("Charlie", "Scope creep never ends."),  # Required seed
    Complaint("Diana", "The waiting time is too long."),
    Complaint("Eve", "The checkout process is confusing."),
]
for seed in seeded:
    complaints.append(seed)

next_direct_id = max((c.id for c in complaints), default=0) + 1

# No need for separate ID assignment loop; ComplaintList.append handles it