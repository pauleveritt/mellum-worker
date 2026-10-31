from fastapi import FastAPI, Form
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from models import Complaint, complaints

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/complaints")
def complaints_board(request: Request):
    return templates.TemplateResponse("complaints.html", {"request": request, "complaints": complaints})

@app.post("/complaints")
async def post_complaint(request: Request, agent_name: str = Form(...), text: str = Form(...)):
    complaint = Complaint(agent_name=agent_name, text=text)
    complaints.append(complaint)
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{complaint_id}/resolve")
async def resolve_complaint(request: Request, complaint_id: int):
    for complaint in complaints:
        if complaint.id == complaint_id:
            complaint.status = "resolved"
            break
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{complaint_id}/reopen")
async def reopen_complaint(request: Request, complaint_id: int):
    for complaint in complaints:
        if complaint.id == complaint_id:
            complaint.status = "open"
            break
    return RedirectResponse(url="/complaints", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", reload=True)