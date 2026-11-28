"""Rendering invoices as text."""


def money(cents: int) -> str:
    return f"R{cents // 100:,}.{cents % 100:02d}"
