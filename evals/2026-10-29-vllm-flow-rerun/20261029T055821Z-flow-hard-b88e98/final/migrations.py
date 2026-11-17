from sqlite_utils import Migrations

migrations = Migrations("agentclinic")

@migrations.register()
def add_tickets_status_archived_index(state):
    state.conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status_archived ON tickets(status, archived_at)")

@migrations.register()
def add_note_column_to_tickets(state):
    # Add note column if not exists
    cursor = state.conn.execute("PRAGMA table_info(tickets)")
    columns = [row[1] for row in cursor.fetchall()]
    if "note" not in columns:
        state.conn.execute("ALTER TABLE tickets ADD COLUMN note TEXT")

@migrations.register()
def backfill_resolved_at(state):
    # Check if column resolved_at exists
    cursor = state.conn.execute("PRAGMA table_info(tickets)")
    columns = [row[1] for row in cursor.fetchall()]
    if "resolved_at" not in columns:
        state.conn.execute("ALTER TABLE tickets ADD COLUMN resolved_at TEXT")
    # Update rows with status='resolved' and resolved_at IS NULL
    state.conn.execute(
        "UPDATE tickets SET resolved_at = ? WHERE status = ? AND resolved_at IS NULL",
        ("2026-01-03T00:00:00", "resolved")
    )

@migrations.register()
def create_open_tickets_view(state):
    # Check if view exists
    cursor = state.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name='open_tickets'"
    )
    if cursor.fetchone() is None:
        state.conn.execute(
            "CREATE VIEW open_tickets AS SELECT * FROM tickets WHERE status = 'open' AND archived_at IS NULL"
        )