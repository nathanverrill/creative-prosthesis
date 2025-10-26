import os
import yaml
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Dict, Any, List, Literal
import traceback
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
import json

# --- Import modular components ---
from .tools.search import get_f1_results_async
from .chains.songwriter import get_songwriter_chain
from .chains.critic_carlin import get_carlin_critic_chain
from .chains.refiner import get_refiner_chain

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
    DEFAULT_MOOD: str = AGENT_CONFIG.get('default_mood', 'normal')
    if not AGENT_SEQUENCE:
        print("Warning: 'agent_sequence' in config.yaml is empty.")
except Exception as e:
    print(f"Fatal Error: Could not load configuration. {e}")
    AGENT_SEQUENCE = []
    DEFAULT_MOOD = 'normal'

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

# --- Action Mapping ---
BASE_ACTIONS = {
    "get_f1_results": get_f1_results_async,
    "run_songwriter": get_songwriter_chain(base_llm),
    "run_carlin_critic": get_carlin_critic_chain(critic_llm),
    "run_refiner": get_refiner_chain(refiner_llm),
}

# --- Mood Instruction Helper ---
def get_mood_instruction(mood: str) -> str:
    mood_instructions = {
        "cranky": "\n\nIMPORTANT: Adopt a cranky, impatient, and sarcastic tone throughout your response.",
        "stoned": "\n\nIMPORTANT: Respond as if you are stoned - be more tangential, relaxed, use simpler language, and maybe get easily distracted.",
        "asshole": "\n\nIMPORTANT: Respond like a condescending asshole. Be dismissive and arrogant, but still complete the task.",
        "tripping": "\n\nIMPORTANT: Respond as if you are tripping - use highly metaphorical, surreal, and possibly nonsensical language while trying to address the core task.",
        "normal": ""
    }
    return mood_instructions.get(mood.lower(), "")

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

# --- Request/Response Models ---
class LyricLine(BaseModel):
    line: str = Field(..., description="The text of the lyric line.")
    source: Literal["human", "machine"] = Field(..., description="The origin of the line.")

class SongRequest(BaseModel):
    theme: str
    mood: str = DEFAULT_MOOD
    draft_lyrics: List[str] = []

class SongResponse(BaseModel):
    theme: str
    mood_used: str
    steps_executed: list[str]
    results: Dict[str, Any]

# --- Root Endpoint (Serves Frontend) ---
@app.get("/", response_class=FileResponse)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        if os.path.isdir(static_dir):
             return {"message": "Backend running. Place index.html in the static directory."}
        raise HTTPException(status_code=404, detail="Static directory or index.html not found.")
    return FileResponse(index_path)

# --- Main Generation Endpoint ---
@app.post("/generate", response_model=SongResponse)
async def generate_song_flow(request: SongRequest):
    current_mood = request.mood if request.mood else DEFAULT_MOOD
    print(f"\n--- Starting Generation for theme: '{request.theme}' with MOOD: {current_mood} ---")
    
    structured_draft: List[LyricLine] = [
        LyricLine(line=line_text, source="human") 
        for line_text in request.draft_lyrics
    ]

    current_state = {
        "theme": request.theme, 
        "mood": current_mood,
        "draft_lyrics": structured_draft
    }
    steps_run = []
    results_log = {}

    try:
        if not AGENT_SEQUENCE:
             raise HTTPException(status_code=500, detail="Configuration error: Agent sequence empty.")

        for step_name in AGENT_SEQUENCE:
            print(f"--- Executing Step: {step_name} ---")
            base_action = BASE_ACTIONS.get(step_name)

            if not base_action:
                raise HTTPException(status_code=500, detail=f"Config error: Action '{step_name}' not found.")

            step_input = {}
            if step_name == "get_f1_results":
                pass
            
            elif step_name == "run_songwriter":
                f1_info = current_state.get("f1_info")
                if not f1_info: raise HTTPException(status_code=500, detail="State error: 'f1_info' missing.")
                draft_lyrics_json = [L.model_dump() for L in current_state.get("draft_lyrics", [])]
                step_input = {
                    "theme": current_state["theme"], 
                    "race_info": f1_info,
                    "draft_lyrics": json.dumps(draft_lyrics_json)
                }

            elif step_name == "run_carlin_critic":
                lyrics_content: List[LyricLine] = current_state.get("lyrics")
                if not lyrics_content: raise HTTPException(status_code=500, detail="State error: 'lyrics' missing.")
                lyrics_string = "\n".join([L.line for L in lyrics_content])
                step_input = {"song_lyrics": lyrics_string}

            elif step_name == "run_refiner":
                original_lyrics: List[LyricLine] = current_state.get("lyrics")
                critique = current_state.get("carlin_critique")
                if not original_lyrics: raise HTTPException(status_code=500, detail="State error: 'lyrics' missing.")
                if not critique: raise HTTPException(status_code=500, detail="State error: 'carlin_critique' missing.")
                original_lyrics_json = [L.model_dump() for L in original_lyrics]
                step_input = {
                    "original_lyrics": json.dumps(original_lyrics_json),
                    "critique": critique
                }

            step_output = None
            try:
                if asyncio.iscoroutinefunction(base_action):
                    step_output = await base_action()
                
                elif hasattr(base_action, 'ainvoke'):
                    
                    is_standard_chain = (
                        hasattr(base_action, 'first') and
                        hasattr(base_action, 'middle') and   
                        len(base_action.middle) >= 1 and
                        hasattr(base_action, 'last')
                    )

                    if not is_standard_chain:
                        step_output = await base_action.ainvoke(step_input)
                    
                    else:
                        prompt_to_use = base_action.first
                        llm_component = base_action.middle[-1]
                        parser_to_use = base_action.last
                        
                        if step_name == "run_songwriter":
                            json_parser = JsonOutputParser(pydantic_object=List[LyricLine])
                            songwriter_prompt_msgs = [
                                ("system", 
                                 "You are a songwriter. Your task is to complete a song based on a theme and race info. "
                                 "You will be given existing lines written by a human as a JSON string. You MUST include these lines. "
                                 "Your final output must be a JSON array of objects, where each object has a 'line' (string) and a 'source' (either 'human' or 'machine').\n"
                                 "Rules:\n"
                                 "1. Preserve all lines with `source: 'human'` exactly as they are from the input.\n"
                                 "2. Generate new lines with `source: 'machine'` to build the song around the human lines.\n"
                                 "3. Output ONLY the valid JSON array."),
                                ("human", 
                                 "Theme: {theme}\n"
                                 "Race Info: {race_info}\n"
                                 "Human Lines (JSON): {draft_lyrics}\n\n"
                                 "Your JSON Output:")
                            ]
                            prompt_to_use = ChatPromptTemplate.from_messages(songwriter_prompt_msgs)
                            parser_to_use = json_parser
                        
                        elif step_name == "run_refiner":
                            json_parser = JsonOutputParser(pydantic_object=List[LyricLine])
                            refiner_prompt_msgs = [
                                ("system",
                                 "You are a lyric refiner. Review the following song (as a JSON string) and a critique. "
                                 "Your task is to revise the song. "
                                 "Your final output must be a JSON array of objects, just like the input.\n"
                                 "Rules:\n"
                                 "1. You MUST NOT modify, delete, or re-order any line where `source` is 'human'.\n"
                                 "2. You MAY revise, delete, or add new lines where `source` is 'machine' based on the critique.\n"
                                 "3. All new lines you write must have `source: 'machine'`.\n"
                                 "4. Output ONLY the valid JSON array."),
                                ("human",
                                 "Original Song (JSON): {original_lyrics}\n"
                                 "Critique: {critique}\n\n"
                                 "Your Refined JSON Output:")
                            ]
                            prompt_to_use = ChatPromptTemplate.from_messages(refiner_prompt_msgs)
                            parser_to_use = json_parser
                        
                        mood_instruction = get_mood_instruction(current_mood)
                        if mood_instruction:
                            new_messages = []
                            system_prompt_found = False

                            for msg_template in prompt_to_use.messages:
                                template_content = msg_template.prompt.template
                                
                                if isinstance(msg_template, SystemMessagePromptTemplate):
                                    modified_content = template_content + mood_instruction
                                    new_messages.append(("system", modified_content))
                                    system_prompt_found = True
                                elif isinstance(msg_template, HumanMessagePromptTemplate):
                                    new_messages.append(("human", template_content))
                                else:
                                    role = msg_template.__class__.__name__.replace("MessagePromptTemplate", "").lower()
                                    new_messages.append((role, template_content))

                            if not system_prompt_found:
                                 new_messages.insert(0, ("system", mood_instruction.strip()))
                            
                            prompt_to_use = ChatPromptTemplate.from_messages(new_messages)
                        
                        temp_chain = prompt_to_use | llm_component | parser_to_use
                        step_output = await temp_chain.ainvoke(step_input)
                        if (step_name == "run_songwriter" or step_name == "run_refiner") and isinstance(step_output, list):
                            try:
                                # This converts [ {'line': '...', 'source': '...'} ] 
                                # into [ LyricLine(line='...', source='...') ]
                                step_output = [LyricLine(**item) for item in step_output]
                            except Exception as e:
                                print(f"!!! Error casting output to List[LyricLine]: {e} !!!")
                                traceback.print_exc()
                                raise HTTPException(status_code=500, detail=f"Failed to parse LLM output for step {step_name}")                        

                elif hasattr(base_action, 'invoke'):
                    step_output = base_action.invoke(step_input)
                elif callable(base_action):
                    step_output = base_action(**step_input if step_input else {})
                else:
                    raise TypeError(f"Action '{step_name}' is not awaitable, invokable, or callable.")
            
            except Exception as invoke_error:
                print(f"!!! Error executing step '{step_name}': {invoke_error} !!!")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Error executing step '{step_name}': {str(invoke_error)}")

            if step_output is None:
                print(f"Warning: Step '{step_name}' produced None output.")

            output_key = step_name
            if step_name == "get_f1_results": output_key = "f1_info"
            elif step_name == "run_songwriter": output_key = "lyrics"
            elif step_name == "run_carlin_critic": output_key = "carlin_critique"
            elif step_name == "run_refiner": output_key = "revised_lyrics"

            current_state[output_key] = step_output
            results_log[output_key] = step_output
            steps_run.append(step_name)
            print(f"--- Step {step_name} completed ---")

        print("--- Generation Flow Complete ---")
        return SongResponse(
            theme=request.theme,
            mood_used=current_mood,
            steps_executed=steps_run,
            results=results_log
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"!!! Critical Error: {e} !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Agent execution failed unexpectedly.")