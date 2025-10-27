# app/graph/state.py
#
# Defines the TypedDict for the LangGraph state.

from typing import TypedDict, List, Dict, Optional, Any

class LyricLine(TypedDict):
    """
    Structure for a single line of lyrics with provenance tracking.
    """
    line: str
    origin: str
    revision_of: Optional[str]
    section: str

class SongWritingState(TypedDict):
    """
    The complete state graph for the songwriting process.
    """
    # --- Core Song Components ---
    topic: str
    creative_plan: Optional[str]
    song_structure: List[str]
    draft_lyrics: List[LyricLine]
    draft_version: int

    # --- Agent-Specific Fields ---
    research_query: Optional[str]
    research_facts: List[str]
    brainstorm_feedback: List[str]
    
    # --- Critic Outputs ---
    critic_scores: Dict[str, float]
    critic_suggestions: List[str]
    qa_status: bool # Fact-check pass/fail

    # --- Graph Control ---
    history: List[str]
    next_step: Optional[str]