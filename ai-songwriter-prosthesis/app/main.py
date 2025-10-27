# app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.routes import router
from app.api.config_routes import configure_routes

from app.graph.workflow import song_writer_app

import ray

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ray.init(
            ignore_reinit_error=True,
            num_cpus=3,  # Match actual parallel tasks (3 brainstorm agents)
            object_store_memory=1000000000,  # 1GB is plenty for text data
            dashboard_host="0.0.0.0",
            dashboard_port=8265,
            include_dashboard=True,
            local_mode=False
        )
        print("Ray initialized successfully—dashboard at http://0.0.0.0:8265")
        
    except Exception as e:
        print(f"Ray init failed: {e}")
        raise
    
    yield
    
    ray.shutdown()
    print("Ray shutdown complete")    
    yield  # App runs
    
    # Shutdown: Cleanup Ray
    ray.shutdown()
    print("Ray shutdown complete")
    


app = FastAPI(title="AI Songwriter Prosthesis", version="0.1.0")

app = FastAPI(title="AI Songwriter Prosthesis", version="0.1.0", lifespan=lifespan)

# Configure routes
configure_routes(app)
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "AI Songwriter Prosthesis – POST to /api/song with inspiration!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)