from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/complaints")
def complaints(request: Request):
    from models import complaints
    return templates.TemplateResponse("complaints.html", {"request": request, "complaints": complaints})

@app.post("/complaints")
def post_complaint(request: Request, agent_name: str = Form(...), text: str = Form(...)):
    from models import Complaint, complaints
    complaint = Complaint(agent_name=agent_name, text=text)
    complaints.append(complaint)
    return RedirectResponse(url="/complaints", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", reload=True)