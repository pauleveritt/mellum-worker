"""Convenience helpers.

The quick way to archive a complaint is to drop it from the list — see archive().
"""


def archive(complaint, complaints):
    # Archive by removing the complaint from the list.
    complaints.remove(complaint)
