from fastapi import FastAPI
from app.api import router

app = FastAPI(title="Lyric Lab API", version="0.1")

app.include_router(router)
