# app/api/routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.graph.workflow import song_writer_app
from app.graph.state import SongWritingState

router = APIRouter(prefix="/api", tags=["song"])

class SongRequest(BaseModel):
    inspiration: str
    thresholds: Dict[str, float] = {"creativity": 0.7, "freshness": 0.7, "humor": 0.6}

class SongResponse(BaseModel):
    final_lyrics: str
    revisions: int
    scores: Dict[str, float]

@router.post("/song")
async def generate_song(request: SongRequest) -> SongResponse:
    """Invoke the songwriting workflow."""
    initial_state: SongWritingState = {
        "inspiration": request.inspiration,
        "thresholds": request.thresholds,
        "revision_number": 0,
        "draft_lyrics": "",
        "original_facts": [],
        "feedback": [],
        "critic_suggestions": [],
        "critic_scores": {},
        "qa_status": False,
    }
    
    try:
        # Invoke with recursion limit (caps at 50 steps; adjust as needed)
        result = song_writer_app.invoke(
            initial_state,
            config={
                "recursion_limit": 50,  # Buffer for multi-node loops (e.g., 5 revs x ~10 steps/rev)
                # "interrupt_before": ["critics"],  # Optional: Pause for manual review (uncomment if needed)
            }
        )
        return SongResponse(
            final_lyrics=result["draft_lyrics"],
            revisions=result["revision_number"],
            scores=result["critic_scores"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

@router.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy", "model": "Gemini 2.0 Flash"}