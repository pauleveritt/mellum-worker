from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from models import complaints, Complaint

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "agentClinic": "AgentClinic"})

@app.get("/complaints")
def complaints_board(request: Request):
    return templates.TemplateResponse("complaints.html", {"request": request, "complaints": complaints})

@app.post("/complaints")
def create_complaint(request: Request, agent_name: str = Form(...), text: str = Form(...)):
    new_complaint = Complaint(agent_name=agent_name, text=text)
    # Assign id if not set (should be set for seeded ones)
    if complaints:
        new_complaint.id = max(c.id for c in complaints) + 1
    else:
        new_complaint.id = 1
    complaints.append(new_complaint)
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{id}/resolve")
def resolve_complaint(request: Request, id: int):
    for complaint in complaints:
        if complaint.id == id:
            complaint.status = "resolved"
            break
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{id}/reopen")
def reopen_complaint(request: Request, id: int):
    for complaint in complaints:
        if complaint.id == id:
            complaint.status = "open"
            break
    return RedirectResponse(url="/complaints", status_code=303)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)