# ==============================================================================
# --- app/api/routes.py (Updated) ---
# ==============================================================================
import itertools
import json
from typing import Dict, Any, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# --- Import New Workflow Components ---
from app.graph.workflow import create_workflow
from app.graph.state import SongWritingState
# --- We need the *definition* of the state's LyricLine TypedDict
from app.graph.state import LyricLine as StateLyricLine 

# --- Pydantic Models for the OLD Frontend ---
# This is the Pydantic model the API *sends* to the frontend.
# We rename it to avoid confusion with the state's TypedDict.
class ApiLyricLine(BaseModel):
    line: str = Field(..., description="The text of the lyric line.")
    source: Literal["human", "machine"] = Field(..., description="The origin of the line.")
    section: str = Field(..., description="Song section (e.g., '[verse 1]', '[chorus]').")

class SongRequestOld(BaseModel):
    theme: str # Maps to 'topic'
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

# --- Compile the graph ---
# We instantiate the graph here when the server starts
song_writer_app = create_workflow()

router = APIRouter(tags=["song"])

# ==============================================================================
# --- Helper Functions (Updated) ---
# ==============================================================================

def map_origin_to_source(origin: str) -> Literal["human", "machine"]:
    """Converts the new 'origin' field to the old 'source' field."""
    if origin and "Human_Input" in origin:
        return "human"
    return "machine"

def map_state_lyrics_to_api_lyrics(
    state_lyrics: List[StateLyricLine]
) -> List[ApiLyricLine]:
    """
    Transforms the graph's List[TypedDict] into the API's List[PydanticModel].
    This is the core compatibility conversion.
    """
    api_lyrics = []
    if not isinstance(state_lyrics, list):
        return []
        
    for item in state_lyrics:
        if not isinstance(item, dict):
            continue
        
        api_lyrics.append(ApiLyricLine(
            line=item.get('line', 'Error: Missing Line'),
            # --- This is the key mapping ---
            source=map_origin_to_source(item.get('origin')),
            section=item.get('section', '[verse 1]')
        ))
    return api_lyrics

def group_lyrics_by_section(
    api_lyrics_list: List[ApiLyricLine]
) -> List[UILyricSection]:
    """Groups the API's flat list of lyrics into sections for the UI."""
    if not api_lyrics_list:
        return []
    
    grouped_sections = []
    # Sort by section to ensure correct grouping
    sorted_lyrics = sorted(api_lyrics_list, key=lambda L: L.section)

    for section_name, group_iter in itertools.groupby(sorted_lyrics, key=lambda L: L.section):
        lines_in_group = [
            UILyricLine(line=L.line, source=L.source) 
            for L in group_iter
        ]
        grouped_sections.append(
            UILyricSection(section=section_name, lines=lines_in_group)
        )
    return grouped_sections

# ==============================================================================
# --- /generate Compatibility Endpoint (Updated) ---
# ==============================================================================

@router.post("/generate", response_model=SongResponseOld)
async def generate_song_flow_old_app(request: SongRequestOld):
    """
    Compatibility layer for the old F1 Lyric Editor frontend.
    Invokes the new agentic workflow.
    """
    
    # 1. --- Map Old Request to New State (CRITICAL UPDATE) ---
    
    # Convert the simple List[str] from the UI into the
    # List[StateLyricLine] TypedDicts that the graph expects.
    initial_human_lyrics: List[StateLyricLine] = [
        {
            "line": line,
            "origin": "Human_Input",
            "revision_of": None,
            "section": "[verse 1]" # Default section for human input
        } 
        for line in request.draft_lyrics if line.strip()
    ]
    
    # This is the correct initial state for our new graph.
    # All other fields are intentionally empty/None as they
    # will be populated by the agents.
    initial_state: SongWritingState = {
        "topic": request.theme,
        "creative_plan": None,
        "song_structure": [],
        "draft_lyrics": initial_human_lyrics,
        "draft_version": 0,
        "research_facts": [],
        "research_query": None,
        "brainstorm_feedback": [],
        "critic_scores": {},
        "critic_suggestions": [],
        "qa_status": False,
        "history": [],
        "next_step": None
    }

    try:
        # 2. Invoke the Graph
        # We use ainvoke because our nodes are async
        final_state = await song_writer_app.ainvoke(
            initial_state,
            config={"recursion_limit": 50}
        )
        
        # 3. --- Extract and Format Final Lyrics (CRITICAL UPDATE) ---
        # Get the final list of TypedDicts from the state
        final_state_lyrics = final_state.get("draft_lyrics", [])
        
        # Convert from state format (TypedDict) to API format (Pydantic)
        final_api_lyrics = map_state_lyrics_to_api_lyrics(final_state_lyrics)
        
        # Group the API lyrics for the UI
        ui_lyrics = group_lyrics_by_section(final_api_lyrics)

        # 4. --- Construct Results Log (CRITICAL UPDATE) ---
        # We now pull from the *correct* state keys
        results_log = {
            "f1_info": final_state.get("research_facts", "No research conducted."), 
            "carlin_critique": final_state.get("critic_suggestions", "No critique generated."), 
            "final_scores": final_state.get("critic_scores", {})
        }

        # 5. Return the Response
        return SongResponseOld(
            theme=request.theme,
            # We can now return the *actual* history from the graph
            steps_executed=final_state.get("history", ["Graph run complete."]), 
            results=results_log,
            lyrics_by_section=ui_lyrics
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error executing songwriting workflow: {str(e)}")