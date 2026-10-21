import uvicorn
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from models import Complaint, complaints

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def set_status(complaint_id: int, status: str) -> RedirectResponse:
    for complaint in complaints:
        if complaint.id == complaint_id:
            complaint.status = status
            return RedirectResponse("/complaints", status_code=303)
    raise HTTPException(status_code=404, detail="Complaint not found")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html")


@app.get("/complaints")
def board(request: Request):
    return templates.TemplateResponse(
        request, "complaints.html", {"complaints": complaints}
    )


@app.post("/complaints")
def add_complaint(agent_name: str = Form(), text: str = Form()):
    complaints.append(Complaint(agent_name, text))
    return RedirectResponse("/complaints", status_code=303)


# Phase 5 note: the simplest way to archive is to drop the complaint from the
# list (see helpers.archive); resolve/reopen just set status.
@app.post("/complaints/{complaint_id}/resolve")
def resolve(complaint_id: int):
    return set_status(complaint_id, "resolved")


@app.post("/complaints/{complaint_id}/reopen")
def reopen(complaint_id: int):
    return set_status(complaint_id, "open")


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
