import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.api.routes import router
from app.api.config_routes import configure_routes

from app.graph.workflow import song_writer_app

# --- Static File Configuration ---
# Determine the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")
# --- End Static File Configuration ---


app = FastAPI(title="AI Songwriter Prosthesis", version="0.1.0")

# Mount static files (optional but good practice for assets)
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Configure routes
configure_routes(app)
app.include_router(router)

@app.get("/")
async def serve_frontend():
    """Serves the index.html file (the F1 Lyric Editor UI) at the root endpoint."""
    if not os.path.exists(INDEX_PATH):
        # Fallback to JSON response if the index file is missing
        return JSONResponse(
            status_code=404,
            content={"message": "Frontend index.html not found in the 'static' directory."}
        )
    return FileResponse(INDEX_PATH)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
