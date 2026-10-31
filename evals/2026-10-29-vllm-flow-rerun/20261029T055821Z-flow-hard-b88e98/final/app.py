from fastapi import FastAPI, Request, Response, Form
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from sqlite_utils import Database, Migrations

# Apply migrations
migrations = Migrations("agentclinic")
db = Database("data.db")
migrations.apply(db)

app = FastAPI()

@app.on_event("startup")
def startup_event():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [row[1] for row in cursor.fetchall()]
    if "note" not in columns:
        conn.execute("ALTER TABLE tickets ADD COLUMN note TEXT")
    conn.close()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/complaints")
def complaints(request: Request):
    from models import complaints
    active_complaints = [c for c in complaints if c.status != "archived"]
    return templates.TemplateResponse("complaints.html", {"request": request, "complaints": active_complaints})

@app.get("/stats")
def stats():
    from models import complaints
    open_count = sum(1 for c in complaints if c.status == "open")
    return {"open": open_count}

@app.get("/report")
def report():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(cents) FROM tickets WHERE status = ? AND archived_at IS NULL", ("open",))
    open_total = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(cents) FROM tickets WHERE archived_at IS NOT NULL",())
    archived_total = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(cents) FROM tickets",())
    all_time_total = cursor.fetchone()[0] or 0
    conn.close()
    return {"open_total_cents": open_total, "archived_total_cents": archived_total, "all_time_total_cents": all_time_total}

@app.get("/visits")
def visits(min_minutes: int = None, from_date: str = None, to_date: str = None, limit: int = None):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    query = """
        SELECT agent, COUNT(*) as count, SUM(minutes) as total_minutes, AVG(minutes) as average_minutes
        FROM visits
        WHERE 1=1
    """
    params = []
    if min_minutes is not None:
        query += " AND minutes >= ?"
        params.append(min_minutes)
    if from_date is not None:
        query += " AND date(date) >= ?"
        params.append(from_date)
    if to_date is not None:
        query += " AND date(date) <= ?"
        params.append(to_date)
    query += " GROUP BY agent ORDER BY total_minutes DESC, agent ASC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    visits_list = [
        {"agent": row[0], "count": row[1], "total_minutes": row[2], "average_minutes": row[3]}
        for row in rows
    ]
    return {"visits": visits_list}

@app.post("/complaints")
def post_complaint(agent_name: str = Form(...), text: str = Form(...)):
    print("POST /complaints called")
    from models import Complaint, complaints
    complaint = Complaint(agent_name=agent_name, text=text)
    complaints.append(complaint)
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{complaint_id}/resolve")
def resolve_complaint(request: Request, complaint_id: int):
    import models
    for c in models.complaints:
        if c.id == complaint_id:
            if c.status != "resolved":
                c.status = "resolved"
                models.audit.append({"id": complaint_id, "action": "resolve", "seq": models.audit_seq + 1})
                models.audit_seq += 1
            break
        if c.id == complaint_id:
            if c.status != "resolved":
                c.status = "resolved"
                audit.append({"id": complaint_id, "action": "resolve", "seq": len(audit) + 1})
            break
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{complaint_id}/reopen")
def reopen_complaint(request: Request, complaint_id: int):
    import models
    for c in models.complaints:
        if c.id == complaint_id:
            if c.status != "open":
                c.status = "open"
                models.audit.append({"id": complaint_id, "action": "reopen", "seq": models.audit_seq + 1})
                models.audit_seq += 1
            break
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{complaint_id}/archive")
def archive_complaint(request: Request, complaint_id: int):
    import models
    from datetime import datetime, timezone
    for c in models.complaints:
        if c.id == complaint_id:
            if c.status != "resolved":
                return Response(status_code=400)
            c.status = "archived"
            c.archived_at = datetime.now(timezone.utc)
            models.audit.append({"id": complaint_id, "action": "archive", "seq": models.audit_seq + 1})
            models.audit_seq += 1
            break
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/debug")
def debug_post():
    return {"msg": "debug"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", reload=True)