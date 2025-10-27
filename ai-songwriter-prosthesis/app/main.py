import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# --- 1. Import OpenTelemetry & Phoenix ---
import phoenix as px
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from openinference.instrumentation.langchain import LangChainInstrumentor

# --- Static File Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")

# --- 2. Launch Phoenix ---
# This starts the Phoenix UI in the background
px.launch()
print("Phoenix Arize UI launched. View traces at http://localhost:6006/")

# --- 3. Configure OpenTelemetry Exporter ---
# This sends trace data to the Phoenix OTLP endpoint
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:6006/v1/traces"
)

# --- 4. Configure Tracer Provider ---
# This is the main OTel object that manages tracing
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# --- 5. Instrument LangChain ---
# This MUST be done *before* the LangChain graph is created.
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
print("LangChain instrumentation complete.")

# --- 6. Import API routes ---
# This import triggers the creation of your `song_writer_app`
# and must happen *after* LangChain is instrumented.
from app.api import routes as api_routes

# --- 7. Create FastAPI App ---
app = FastAPI(title="AI Songwriter Prosthesis", version="0.1.0")

# --- 8. Instrument FastAPI ---
# This automatically traces all web requests
FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
print("FastAPI instrumentation complete.")

# --- Mount static files ---
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    print(f"Warning: Static directory not found at {STATIC_DIR}")

# --- Include API routes with a prefix ---
app.include_router(api_routes.router, prefix="/api")
print("API routes included.")

# --- Serve Frontend at Root ---
@app.get("/")
async def serve_frontend():
    """Serves the index.html file (the F1 Lyric Editor UI) at the root endpoint."""
    if not os.path.exists(INDEX_PATH):
        print(f"Error: index.html not found at {INDEX_PATH}")
        return JSONResponse(
            status_code=404,
            content={"message": "Frontend index.html not found in the 'static' directory."}
        )
    return FileResponse(INDEX_PATH)

# --- Main entry point ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)