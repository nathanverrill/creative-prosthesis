# app/graph/state.py

from typing import TypedDict, Dict, Any, List, Annotated
from operator import add

class SongWritingState(TypedDict):
    """Shared state schema for the LangGraph workflow."""
    inspiration: str
    thresholds: Dict[str, float]  # e.g., {"creativity": 0.8, "freshness": 0.7, "humor": 0.6}
    revision_number: int
    draft_lyrics: str
    original_facts: List[str]
    feedback: Annotated[List[str], add]  # Allows parallel nodes to append concurrently
    critic_suggestions: List[str]
    critic_scores: Dict[str, float]  # e.g., {"creativity": 0.85, "freshness": 0.75, "humor": 0.65}
    qa_status: bool  # Fact-check pass