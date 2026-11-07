from fastapi import FastAPI
from starlette.templating import Jinja2Templates
from starlette.requests import Request
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, host="0.0.0.0", port=8000)