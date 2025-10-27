# app/api/config_routes.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def configure_routes(app: FastAPI):
    """Apply global middleware/config to routes."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Add auth/JWT here if needed
    print("Routes configured with CORS.")