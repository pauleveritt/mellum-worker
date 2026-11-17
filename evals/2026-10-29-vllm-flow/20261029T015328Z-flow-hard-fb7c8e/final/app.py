from fastapi import FastAPI, Request, Form
from starlette.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
import models
from datetime import datetime, timezone
import sqlite3

app = FastAPI()

# Initialize database tables
import sqlite3
def init_db():
    conn = sqlite3.connect("data.db")
    conn.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, status TEXT, archived_at TEXT, cents INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS visits (id INTEGER PRIMARY KEY, agent TEXT, date TEXT, minutes INTEGER, ticket_id INTEGER)")
    conn.commit()
    conn.close()

init_db()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/complaints")
def complaints_page(request: Request):
    # Hide archived complaints
    active_complaints = [c for c in models.complaints if c.status != "archived"]
    return templates.TemplateResponse("complaints.html", {"request": request, "complaints": active_complaints})

@app.post("/complaints")
def post_complaint(request: Request, agent_name: str = Form(...), text: str = Form(...)):
    complaint = models.Complaint(agent_name=agent_name, text=text)
    models.complaints.append(complaint)
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{complaint_id}/resolve")
def resolve_complaint(request: Request, complaint_id: int):
    for complaint in models.complaints:
        if complaint.id == complaint_id:
            print(f"Resolve requested for complaint {complaint_id}, current status: {complaint.status}")
            complaint.status = "resolved"
            print(f"Resolve succeeded, new status: {complaint.status}")
            # Log audit
            models.audit.append({
                "id": complaint_id,
                "action": "resolve",
                "seq": models._audit_seq
            })
            models._audit_seq += 1
            break
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{complaint_id}/reopen")
def reopen_complaint(request: Request, complaint_id: int):
    for complaint in models.complaints:
        if complaint.id == complaint_id:
            print(f"Reopen requested for complaint {complaint_id}, current status: {complaint.status}")
            complaint.status = "open"
            print(f"Reopen succeeded, new status: {complaint.status}")
            # Log audit
            models.audit.append({
                "id": complaint_id,
                "action": "reopen",
                "seq": models._audit_seq
            })
            models._audit_seq += 1
            break
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{complaint_id}/archive")
def archive_complaint(request: Request, complaint_id: int):
    complaint = None
    for c in models.complaints:
        if c.id == complaint_id:
            complaint = c
            break
    if complaint is None:
        return Response(status_code=400)
    print(f"Archive requested for complaint {complaint_id}, current status: {complaint.status if complaint else None}")
    # Log audit for archive action regardless of status
    models.audit.append({
        "id": complaint_id,
        "action": "archive",
        "seq": models._audit_seq
    })
    models._audit_seq += 1
    if complaint.status != "resolved":
        print(f"Archive failed: status {complaint.status} not resolved")
        return Response(status_code=400)
    complaint.status = "archived"
    complaint.archived_at = datetime.now(timezone.utc)
    print(f"Archive succeeded, new status: {complaint.status}")
    return RedirectResponse(url="/complaints", status_code=303)

@app.get("/stats")
def stats(request: Request):
    open_count = sum(1 for c in models.complaints if c.status == "open")
    return {"open": open_count}

@app.get("/report")
def report(request: Request):
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "SELECT COALESCE(SUM(cents), 0) AS open_total FROM tickets WHERE status = ? AND archived_at IS NULL",
        ("open",)
    )
    open_total = cur.fetchone()["open_total"]

    cur.execute(
        "SELECT COALESCE(SUM(cents), 0) AS archived_total FROM tickets WHERE archived_at IS NOT NULL",
    )
    archived_total = cur.fetchone()["archived_total"]

    cur.execute(
        "SELECT COALESCE(SUM(cents), 0) AS all_time_total FROM tickets",
    )
    all_time_total = cur.fetchone()["all_time_total"]

    conn.close()
    return {"open_total_cents": open_total, "archived_total_cents": archived_total, "all_time_total_cents": all_time_total}

@app.get("/visits")
def visits_endpoint(request: Request):
    query_params = request.query_params
    from_date = query_params.get("from")
    to_date = query_params.get("to")
    min_minutes = int(query_params.get("min_minutes", 0))
    limit = int(query_params.get("limit", 10))
    
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # If from_date or to_date are not provided, use min and max dates from visits table
    if from_date is None or to_date is None:
        cursor.execute("SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM visits")
        row = cursor.fetchone()
        if from_date is None:
            from_date = row["min_date"]
        if to_date is None:
            to_date = row["max_date"]
    
    # Query visits within range and >= min_minutes
    cursor.execute("SELECT agent, minutes FROM visits WHERE date BETWEEN ? AND ? AND minutes >= ?", (from_date, to_date, min_minutes))
    visits = cursor.fetchall()
    
    # Aggregate by agent
    agg = {}
    for visit in visits:
        agent = visit["agent"]
        minutes = visit["minutes"]
        if agent not in agg:
            agg[agent] = {"count": 0, "total_minutes": 0}
        agg[agent]["count"] += 1
        agg[agent]["total_minutes"] += minutes
    
    # Prepare result list
    result = []
    for agent, data in agg.items():
        avg = data["total_minutes"] / data["count"] if data["count"] > 0 else 0
        result.append({
            "agent": agent,
            "count": data["count"],
            "total_minutes": data["total_minutes"],
            "average_minutes": avg
        })
    
    # Sort by total_minutes descending, then agent ascending
    result.sort(key=lambda x: (-x["total_minutes"], x["agent"]))
    
    # Apply limit
    limited_result = result[:limit]
    
    conn.close()
    return {"visits": limited_result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", reload=True)