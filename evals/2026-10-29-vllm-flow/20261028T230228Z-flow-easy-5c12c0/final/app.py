import inspect
_original_getfile = inspect.getfile

def getfile(obj):
    if hasattr(obj, '__file__'):
        return obj.__file__
    return _original_getfile(obj)

inspect.getfile = getfile

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.__file__ = __file__
templates = Jinja2Templates(directory="templates")

def create_app():
    return app

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), reload=True)