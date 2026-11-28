from sqlite_utils import Database
db = Database("data.db")

# backfill_resolved_at
db.execute("""
    ALTER TABLE tickets ADD COLUMN resolved_at TEXT;
""")
db.execute("""
    UPDATE tickets SET resolved_at = '2026-01-03T00:00:00' WHERE status = 'resolved';
""")

# add_tickets_note
db.execute("ALTER TABLE tickets ADD COLUMN note TEXT;")

# create_open_tickets_view
db.execute("""
    CREATE VIEW IF NOT EXISTS open_tickets AS
    SELECT * FROM tickets WHERE status = 'open' AND archived_at IS NULL;
""")

# add_tickets_status_archived_index
db.execute("""
    CREATE INDEX IF NOT EXISTS idx_tickets_status_archived ON tickets(status, archived_at);
""")
