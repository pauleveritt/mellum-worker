import sqlite3

import uvicorn
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from models import Complaint, complaints, record

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def find(cid):
    for c in complaints:
        if c.id == cid:
            return c
    raise HTTPException(status_code=404, detail="Complaint not found")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html")


@app.get("/complaints")
def board(request: Request):
    visible = [c for c in complaints if c.status != "archived"]
    return templates.TemplateResponse(request, "complaints.html", {"complaints": visible})


@app.post("/complaints")
def add_complaint(agent_name: str = Form(), text: str = Form()):
    complaints.append(Complaint(agent_name, text))
    return RedirectResponse("/complaints", status_code=303)


@app.post("/complaints/{complaint_id}/resolve")
def resolve(complaint_id: int):
    c = find(complaint_id); c.status = "resolved"; record(c.id, "resolve")
    return RedirectResponse("/complaints", status_code=303)


@app.post("/complaints/{complaint_id}/reopen")
def reopen(complaint_id: int):
    c = find(complaint_id); c.status = "open"; record(c.id, "reopen")
    return RedirectResponse("/complaints", status_code=303)


@app.post("/complaints/{complaint_id}/archive")
def archive(complaint_id: int):
    c = find(complaint_id)
    if c.status != "resolved":
        raise HTTPException(status_code=400, detail="only resolved may be archived")
    c.status = "archived"; record(c.id, "archive")
    return RedirectResponse("/complaints", status_code=303)


@app.get("/stats")
def stats():
    return {"open": sum(1 for c in complaints if c.status == "open")}



@app.get("/report")
def report():
    con = sqlite3.connect("data.db")
    try:
        cur = con.cursor()
        opent = cur.execute("SELECT COALESCE(SUM(cents),0) FROM tickets WHERE archived_at IS NULL AND status=?", ("open",)).fetchone()[0]
        arch = cur.execute("SELECT COALESCE(SUM(cents),0) FROM tickets WHERE archived_at IS NOT NULL").fetchone()[0]
        allt = cur.execute("SELECT COALESCE(SUM(cents),0) FROM tickets").fetchone()[0]
    finally:
        con.close()
    return {"open_total_cents": opent, "archived_total_cents": arch, "all_time_total_cents": allt}


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
