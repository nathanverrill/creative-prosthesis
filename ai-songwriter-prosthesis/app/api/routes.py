import itertools
import json
from operator import itemgetter
from typing import Dict, Any, List, Literal, Optional, TypedDict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# --- Import New Workflow Components (Adjust these paths as necessary) ---
# Assuming these are imported from where your new workflow is defined:
from app.graph.workflow import song_writer_app 
from app.graph.state import SongWritingState 

# --- Pydantic Model for Structured Output (MUST match Collaborator output) ---
class LyricLine(BaseModel):
    line: str = Field(..., description="The text of the lyric line.")
    source: Literal["human", "machine"] = Field(..., description="The origin of the line.")
    section: str = Field(..., description="Song section (e.g., '[verse 1]', '[chorus]').")

# --- Compatibility Models (for the Old F1 Frontend) ---
class SongRequestOld(BaseModel):
    theme: str # Maps to 'inspiration'
    mood: str = "normal" 
    draft_lyrics: List[str] = [] # Lines marked as 'human'

class UILyricLine(BaseModel):
    line: str
    source: Literal["human", "machine"]

class UILyricSection(BaseModel):
    section: str
    lines: List[UILyricLine]

class SongResponseOld(BaseModel):
    theme: str
    steps_executed: list[str]
    results: Dict[str, Any]
    lyrics_by_section: List[UILyricSection] = []

# --- TypedDict for LangGraph State (Copied for reference) ---
class AgentState(TypedDict):
    theme: str
    draft_lyrics: List[LyricLine]
    steps_executed: List[str]
    f1_info: Optional[Any]
    lyrics: Optional[List[LyricLine]]
    carlin_critique: Optional[str]
    revised_lyrics: Optional[List[LyricLine]]
    error: Optional[str]

router = APIRouter(tags=["song"])

# ==============================================================================
# --- Helper Functions (Essential for transformation) ---
# ==============================================================================

def group_lyrics_by_section(lyrics_list: List[LyricLine]) -> List[UILyricSection]:
    """Transforms a flat List[LyricLine] into a nested list grouped by section."""
    if not lyrics_list:
        return []
    
    grouped_sections = []
    # Sort by section to ensure correct grouping
    sorted_lyrics = sorted(lyrics_list, key=lambda L: L.section)

    for section_name, group_iter in itertools.groupby(sorted_lyrics, key=lambda L: L.section):
        lines_in_group = [
            UILyricLine(line=L.line, source=L.source) 
            for L in group_iter
        ]
        grouped_sections.append(
            UILyricSection(section=section_name, lines=lines_in_group)
        )
        
    return grouped_sections

def extract_final_lyrics(state: SongWritingState) -> List[LyricLine]:
    """
    Extracts the final structured lyrics from the new workflow's state,
    and defensively cleans up malformed dictionaries.
    """
    lyrics_data = state.get("draft_lyrics")
    
    if isinstance(lyrics_data, str):
        try:
            # Attempt to parse it as the expected JSON List[LyricLine]
            parsed = json.loads(lyrics_data)
            lyrics_data = parsed
        except (json.JSONDecodeError, TypeError):
            # Fallback for simple string output (e.g., from an error)
            lines = lyrics_data.split('\n')
            return [LyricLine(line=line.strip(), source="machine", section="[verse 1]") 
                    for line in lines if line.strip()]

    # If the state holds the list of dictionaries
    if isinstance(lyrics_data, list):
        cleaned_lyrics = []
        for item in lyrics_data:
            if not isinstance(item, dict):
                continue
            
            # --- CRITICAL FIX: Supply default values if keys are missing ---
            cleaned_lyrics.append(LyricLine(
                line=item.get('line', 'Error: Missing Line Content'),
                source=item.get('source', 'machine'),
                section=item.get('section', '[verse 1]') # Default to [verse 1] if missing
            ))
        return cleaned_lyrics
        
    return []

# ==============================================================================
# --- /generate Compatibility Endpoint (Root path as per old frontend JS) ---
# ==============================================================================

@router.post("/generate", response_model=SongResponseOld)
async def generate_song_flow_old_app(request: SongRequestOld):
    """
    Compatibility layer for the old F1 Lyric Editor frontend.
    Invokes the new, generic, iterative songwriting workflow.
    """
    
    # 1. Map Old Request to New State
    initial_state: SongWritingState = {
        "inspiration": request.theme, 
        "draft_lyrics": "\n".join(request.draft_lyrics), 
        "revision_number": 0,
        "thresholds": {"creativity": 0.5, "freshness": 0.5, "humor": 0.4},
        "original_facts": [],
        "feedback": [],
        "critic_suggestions": [],
        "critic_scores": {},
        "qa_status": False,
        "current_revision_lyrics": "\n".join(request.draft_lyrics)
    }

    try:
        # 2. Invoke the Graph (runs the full iterative workflow)
        final_state = await song_writer_app.ainvoke(
            initial_state,
            config={"recursion_limit": 50}
        )
        
        # 3. Extract and Format Final Lyrics
        # This function now handles the malformed dictionary error.
        final_lyrics_list: List[LyricLine] = extract_final_lyrics(final_state)
        ui_lyrics = group_lyrics_by_section(final_lyrics_list)

        # 4. Construct Results Log
        results_log = {
            "f1_info": final_state.get("original_facts", "Research data not available."), 
            "carlin_critique": final_state.get("critic_suggestions", "No critique generated."), 
            "final_scores": final_state.get("critic_scores", {})
        }

        # 5. Return the Response
        return SongResponseOld(
            theme=request.theme,
            steps_executed=[
                "researcher", 
                "collaborator", 
                "brainstorm (parallel)",
                "fact_check",
                f"critics ({final_state.get('revision_number', 0)} revisions)"
            ], 
            results=results_log,
            lyrics_by_section=ui_lyrics
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error executing songwriting workflow: {str(e)}")

# Add the new /song endpoint for the modern API if it exists (placeholder below)
# @router.post("/song")
# async def generate_song(request: SongRequest) -> SongResponse:
#     ...
