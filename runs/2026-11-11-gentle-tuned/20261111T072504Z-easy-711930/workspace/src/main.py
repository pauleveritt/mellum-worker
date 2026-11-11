from fastapi import FastAPI
from src.routes import home

app = FastAPI()

app.include_router(home.router)