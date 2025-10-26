import os
import yaml
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
# --- LangGraph Imports ---
from typing import Dict, Any, List, Literal, TypedDict, Optional
from langgraph.graph import StateGraph, END
# --- End LangGraph Imports ---
import traceback
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import itertools
from operator import itemgetter

# --- Import modular components ---
from .tools.search import get_f1_results_async
from .chains.critic_carlin import get_carlin_critic_chain

# --- Configuration Loading ---
def load_config(config_path="config.yaml") -> Dict:
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_config_path = os.path.join(base_dir, config_path)
        with open(full_config_path, 'r') as f:
            config = yaml.safe_load(f)
        if not config or 'agent_sequence' not in config:
             raise ValueError("Config file is empty or missing 'agent_sequence' key.")
        return config
    except FileNotFoundError:
        print(f"!!! Error: Config file not found at {full_config_path} !!!")
        raise
    except Exception as e:
        print(f"!!! Error loading config file: {e} !!!")
        raise

try:
    AGENT_CONFIG = load_config()
    AGENT_SEQUENCE: List[str] = AGENT_CONFIG.get('agent_sequence', [])
    if not AGENT_SEQUENCE:
        print("Warning: 'agent_sequence' in config.yaml is empty.")
except Exception as e:
    print(f"Fatal Error: Could not load configuration. {e}")
    AGENT_SEQUENCE = []

# --- LangChain/LLM Setup ---
load_dotenv()
gemini_api_key = os.getenv("GOOGLE_API_KEY")
if not gemini_api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

try:
    base_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key)
    critic_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key, temperature=0.7)
    refiner_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key, temperature=0.5)
except Exception as e:
    print(f"!!! Error initializing LLMs: {e} !!!")
    raise

# --- Global Chains ---
carlin_critic_chain = get_carlin_critic_chain(critic_llm)

# Songwriter Chain
songwriter_json_parser = JsonOutputParser(pydantic_object=List['LyricLine'])
songwriter_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a songwriter. Your task is to complete a song... "
     "Your final output must be a JSON array of objects, where each object has a 'line', 'source', and 'section'.\n"
     "Rules:\n"
     "1. You MUST include all lines where `source: 'human'`. You must NOT modify their 'line' or 'source' attributes.\n"
     "2. Human lines are given a default 'section' (e.g., `\"[verse 1]\"`). You SHOULD change this 'section' tag to a more logical one (e.g., `\"[chorus]\"`) if your song structure demands it.\n"
     "3. ALL lines in your final output (both human and machine) MUST have a 'section' field populated with a standard Suno-style tag, like `\"[intro]\"`, `\"[verse 1]\"`, `\"[chorus]\"`, `\"[verse 2]\"`, `\"[bridge]\"`, or `\"[outro]\"`.\n"
     "4. All new lines you write must have `source: 'machine'` and a valid 'section' tag (e.g., `\"[chorus]\"`).\n"
     "5. Output ONLY the valid JSON array."),
    ("human", 
     "Theme: {theme}\n"
     "Race Info: {race_info}\n"
     "Human Lines (JSON): {draft_lyrics}\n\n"
     "Your JSON Output:")
])
songwriter_chain = songwriter_prompt | base_llm | songwriter_json_parser

# Refiner Chain
refiner_json_parser = JsonOutputParser(pydantic_object=List['LyricLine'])
refiner_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a lyric refiner. Review the following song (as a JSON string) and a critique. "
     "Your task is to revise the song. "
     "Your final output must be a JSON array of objects, just like the input.\n"
     "Rules:\n"
     "1. You MUST NOT modify, delete, or re-order any line where `source` is 'human'. This includes its 'line' and 'section' attributes. They are locked.\n"
     "2. You MAY revise, delete, or add new lines where `source` is 'machine' based on the critique.\n"
     "3. You MAY change the 'section' tag of 'machine' lines if the critique suggests a structural change (e.g., move a machine line from `\"[verse 1]\"` to `\"[bridge]\"`).\n"
     "4. All new lines you write must have `source: 'machine'` and a valid 'section' tag (e.g., `\"[verse 1]\"`).\n"
     "5. Output ONLY the valid JSON array."),
    ("human",
     "Original Song (JSON): {original_lyrics}\n"
     "Critique: {critique}\n\n"
     "Your Refined JSON Output:")
])
refiner_chain = refiner_prompt | refiner_llm | refiner_json_parser

# --- Helper function for Critic Formatting ---
def format_lyrics_with_sections(lyrics: List['LyricLine']) -> str:
    """Converts a List[LyricLine] into a string with section headers."""
    if not lyrics:
        return "No lyrics provided."
    
    formatted_lyrics = []
    current_section = None
    
    for L in lyrics:
        if L.section != current_section:
            if current_section is not None:
                formatted_lyrics.append("")
            formatted_lyrics.append(L.section.strip())
            current_section = L.section
        
        formatted_lyrics.append(L.line)
        
    return "\n".join(formatted_lyrics)

# --- Helper function for UI Formatting ---
def group_lyrics_by_section(lyrics_list: List['LyricLine']) -> List['UILyricSection']:
    """
    Transforms a flat List[LyricLine] into a nested list grouped by section,
    perfect for a UI.
    """
    if not lyrics_list:
        return []

    grouped_sections = []
    
    for section_name, group_iter in itertools.groupby(lyrics_list, key=lambda L: L.section):
        lines_in_group = [
            UILyricLine(line=L.line, source=L.source) 
            for L in group_iter
        ]
        grouped_sections.append(
            UILyricSection(section=section_name, lines=lines_in_group)
        )
        
    return grouped_sections

# --- FastAPI App Initialization ---
app = FastAPI(title="F1 Songwriting Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files Setup ---
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if not os.path.isdir(static_dir):
    print(f"Warning: Static directory not found at {static_dir}. Frontend will not be served.")
else:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- Request/Response Models (Pydantic) ---
class LyricLine(BaseModel):
    line: str = Field(..., description="The text of the lyric line.")
    source: Literal["human", "machine"] = Field(..., description="The origin of the line.")
    section: str = Field(..., description="Song section (e.g., '[verse 1]', '[chorus]', '[bridge]').")

class SongRequest(BaseModel):
    theme: str
    draft_lyrics: List[str] = []

# --- UI-Specific Models ---
class UILyricLine(BaseModel):
    line: str
    source: Literal["human", "machine"]

class UILyricSection(BaseModel):
    section: str
    lines: List[UILyricLine]

class SongResponse(BaseModel):
    theme: str
    steps_executed: list[str]
    results: Dict[str, Any]
    lyrics_by_section: List[UILyricSection] = []

# --- Root Endpoint (Serves Frontend) ---
@app.get("/", response_class=FileResponse)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        if os.path.isdir(static_dir):
             return {"message": "Backend running. Place index.html in the static directory."}
        raise HTTPException(status_code=404, detail="Static directory or index.html not found.")
    return FileResponse(index_path)


# ==============================================================================
# --- LANGGRAPH STATE DEFINITION ---
# ==============================================================================

class AgentState(TypedDict):
    # Initial inputs
    theme: str
    draft_lyrics: List[LyricLine]
    
    # List of steps run
    steps_executed: List[str]
    
    # Results from each step
    f1_info: Optional[Any]
    lyrics: Optional[List[LyricLine]]
    carlin_critique: Optional[str]
    revised_lyrics: Optional[Optional[List[LyricLine]]]
    # Error handling
    error: Optional[str]


# ==============================================================================
# --- LANGGRAPH NODE FUNCTIONS ---
# ==============================================================================

async def get_f1_results_node(state: AgentState) -> Dict[str, Any]:
    """Node to fetch F1 race results."""
    print("--- Executing Step: get_f1_results ---")
    try:
        f1_info = await get_f1_results_async()
        return {
            "f1_info": f1_info,
            "steps_executed": state.get("steps_executed", []) + ["get_f1_results"]
        }
    except Exception as e:
        print(f"!!! Error in get_f1_results_node: {e} !!!")
        traceback.print_exc()
        return {
            "error": f"Error executing step 'get_f1_results': {str(e)}",
            "steps_executed": state.get("steps_executed", []) + ["get_f1_results"]
        }

async def run_songwriter_node(state: AgentState) -> Dict[str, Any]:
    """Node to run the initial songwriting chain."""
    print("--- Executing Step: run_songwriter ---")
    try:
        # 1. Get inputs from state
        theme = state["theme"]
        f1_info = state.get("f1_info")
        draft_lyrics = state.get("draft_lyrics", [])
        
        if not f1_info:
            raise ValueError("State error: 'f1_info' missing for songwriter.")
            
        draft_lyrics_json = json.dumps([L.model_dump() for L in draft_lyrics])
        step_input = {
            "theme": theme, 
            "race_info": f1_info,
            "draft_lyrics": draft_lyrics_json
        }

        # 2. Invoke global chain
        step_output = await songwriter_chain.ainvoke(step_input)

        # 3. Cast List[dict] to List[LyricLine]
        if isinstance(step_output, list):
            step_output = [LyricLine(**item) for item in step_output]
        else:
             raise TypeError(f"Songwriter output was not a list, but {type(step_output)}")

        return {
            "lyrics": step_output,
            "steps_executed": state.get("steps_executed", []) + ["run_songwriter"]
        }

    except Exception as e:
        print(f"!!! Error in run_songwriter_node: {e} !!!")
        traceback.print_exc()
        return {
            "error": f"Error executing step 'run_songwriter': {str(e)}",
            "steps_executed": state.get("steps_executed", []) + ["run_songwriter"]
        }

async def run_carlin_critic_node(state: AgentState) -> Dict[str, Any]:
    """Node to run the critic chain."""
    print("--- Executing Step: run_carlin_critic ---")
    try:
        # 1. Get inputs from state
        lyrics_content: List[LyricLine] = state.get("lyrics")
        
        if not lyrics_content:
            raise ValueError("State error: 'lyrics' missing for critic.")
        
        lyrics_string = format_lyrics_with_sections(lyrics_content)
        step_input = {"song_lyrics": lyrics_string}

        # 2. Invoke global chain
        step_output = await carlin_critic_chain.ainvoke(step_input)
        
        return {
            "carlin_critique": step_output,
            "steps_executed": state.get("steps_executed", []) + ["run_carlin_critic"]
        }

    except Exception as e:
        print(f"!!! Error in run_carlin_critic_node: {e} !!!")
        traceback.print_exc()
        return {
            "error": f"Error executing step 'run_carlin_critic': {str(e)}",
            "steps_executed": state.get("steps_executed", []) + ["run_carlin_critic"]
        }

async def run_refiner_node(state: AgentState) -> Dict[str, Any]:
    """Node to run the refiner chain."""
    print("--- Executing Step: run_refiner ---")
    try:
        # 1. Get inputs from state
        original_lyrics: List[LyricLine] = state.get("lyrics")
        critique = state.get("carlin_critique")

        if not original_lyrics:
            raise ValueError("State error: 'lyrics' missing for refiner.")
        if not critique:
            raise ValueError("State error: 'carlin_critique' missing for refiner.")
            
        original_lyrics_json = json.dumps([L.model_dump() for L in original_lyrics])
        step_input = {
            "original_lyrics": original_lyrics_json,
            "critique": critique
        }

        # 2. Invoke global chain
        step_output = await refiner_chain.ainvoke(step_input)
        
        # 3. Cast List[dict] to List[LyricLine]
        if isinstance(step_output, list):
            step_output = [LyricLine(**item) for item in step_output]
        else:
             raise TypeError(f"Refiner output was not a list, but {type(step_output)}")

        return {
            "revised_lyrics": step_output,
            "steps_executed": state.get("steps_executed", []) + ["run_refiner"]
        }

    except Exception as e:
        print(f"!!! Error in run_refiner_node: {e} !!!")
        traceback.print_exc()
        return {
            "error": f"Error executing step 'run_refiner': {str(e)}",
            "steps_executed": state.get("steps_executed", []) + ["run_refiner"]
        }


# ==============================================================================
# --- LANGGRAPH GRAPH DEFINITION & COMPILATION ---
# ==============================================================================

workflow = StateGraph(AgentState)

# Map node names from config to the async functions
NODE_MAP = {
    "get_f1_results": get_f1_results_node,
    "run_songwriter": run_songwriter_node,
    "run_carlin_critic": run_carlin_critic_node,
    "run_refiner": run_refiner_node,
}

# Add all nodes defined in the config
for step_name in AGENT_SEQUENCE:
    if step_name in NODE_MAP:
        workflow.add_node(step_name, NODE_MAP[step_name])
        print(f"Added node: {step_name}")
    else:
        print(f"Warning: Step '{step_name}' in config.yaml not found in NODE_MAP.")

# Add edges in sequence
if AGENT_SEQUENCE:
    # Set the entry point to the first step
    workflow.set_entry_point(AGENT_SEQUENCE[0])
    print(f"Set entry point: {AGENT_SEQUENCE[0]}")
    
    # Add sequential edges
    for i in range(len(AGENT_SEQUENCE) - 1):
        current_step = AGENT_SEQUENCE[i]
        next_step = AGENT_SEQUENCE[i+1]
        
        if current_step in NODE_MAP and next_step in NODE_MAP:
            workflow.add_edge(current_step, next_step)
            print(f"Added edge: {current_step} -> {next_step}")
    
    # Add edge from last node to END
    last_step = AGENT_SEQUENCE[-1]
    if last_step in NODE_MAP:
        workflow.add_edge(last_step, END)
        print(f"Added edge: {last_step} -> END")
else:
    raise ValueError("Cannot build graph: AGENT_SEQUENCE in config.yaml is empty.")

# Compile the graph
print("Compiling graph...")
graph_app = workflow.compile()
print("Graph compiled successfully.")


# ==============================================================================
# --- MAIN FASTAPI GENERATION ENDPOINT (NOW USING LANGGRAPH) ---
# ==============================================================================

@app.post("/generate", response_model=SongResponse)
async def generate_song_flow(request: SongRequest):
    print(f"\n--- Starting Generation for theme: '{request.theme}' ---")
    
    # 1. Prepare initial state
    structured_draft: List[LyricLine] = [
        LyricLine(line=line_text, source="human", section="[verse 1]") 
        for line_text in request.draft_lyrics
    ]

    initial_state: AgentState = {
        "theme": request.theme,
        "draft_lyrics": structured_draft,
        "steps_executed": [],
        "f1_info": None,
        "lyrics": None,
        "carlin_critique": None,
        "revised_lyrics": None,
        "error": None
    }

    try:
        # 2. Invoke the graph
        print("--- Invoking LangGraph ---")
        final_state = await graph_app.ainvoke(initial_state)
        print("--- LangGraph Execution Complete ---")

        # 3. Check for errors
        error = final_state.get("error")
        if error:
            raise HTTPException(status_code=500, detail=error)

        # 4. Process final state
        # Get the final lyrics (either revised or original)
        final_lyrics_list: List[LyricLine] = final_state.get(
            "revised_lyrics", 
            final_state.get("lyrics", [])
        )

        # Transform the flat list into a nested, UI-friendly list
        ui_lyrics = group_lyrics_by_section(final_lyrics_list)

        # Create results log for debugging/display
        results_log = {
            "f1_info": final_state.get("f1_info"),
            "lyrics": final_state.get("lyrics"),
            "carlin_critique": final_state.get("carlin_critique"),
            "revised_lyrics": final_state.get("revised_lyrics")
        }

        # 5. Return the response
        return SongResponse(
            theme=request.theme,
            steps_executed=final_state.get("steps_executed", []),
            results=results_log,
            lyrics_by_section=ui_lyrics
        )
        
    except HTTPException:
        # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        # Handle graph execution errors
        print(f"!!! Critical Error during graph execution: {e} !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error during song generation: {str(e)}")
