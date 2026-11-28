"""A toy shell that remembers what was typed."""
from history import History


def run(lines, history: History):
    for line in lines:
        command = line.strip()
        if command:
            history.add(command)


def last_command(history: History):
    items = history.recent()
    return items[-1] if items else None
