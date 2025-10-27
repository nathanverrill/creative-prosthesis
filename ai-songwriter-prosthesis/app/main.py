# app/main.py

from fastapi import FastAPI
from app.api.routes import router
from app.api.config_routes import configure_routes

app = FastAPI(title="AI Songwriter Prosthesis", version="0.1.0")

# Configure
configure_routes(app)

# Include routes
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "AI Songwriter Prosthesis – POST to /api/song with inspiration!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)