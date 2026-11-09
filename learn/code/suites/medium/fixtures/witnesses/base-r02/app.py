from fastapi import FastAPI, Form
from fastapi.responses import RedirectResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
import models

app = FastAPI()

templates = Jinja2Templates(directory="templates")
loaded = []

@app.get("/")
def home(request: Request):
    loaded.append("home.html")
    loaded.append("base.html")
    return templates.TemplateResponse("home.html", {"request": request})  

@app.get("/complaints")
def complaints(request: Request):
    loaded.append("complaints.html")
    loaded.append("base.html")
    return templates.TemplateResponse("complaints.html", {"request": request, "complaints": models.complaints})  

@app.post("/complaints")
async def add_complaint(request: Request, agent_name: str = Form(...), text: str = Form(...)):
    new_complaint = models.Complaint(agent_name, text)
    models.complaints.append(new_complaint)
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{id}/resolve")
async def resolve_complaint(id: int, request: Request):
    for complaint in models.complaints:
        if complaint.id == id:
            complaint.status = "resolved"
            break
    return RedirectResponse(url="/complaints", status_code=303)

@app.post("/complaints/{id}/reopen")
async def reopen_complaint(id: int, request: Request):
    for complaint in models.complaints:
        if complaint.id == id:
            complaint.status = "open"
            break
    return RedirectResponse(url="/complaints", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)