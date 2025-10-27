# ==============================================================================
# --- app/agents/collaborator.py ---
# ==============================================================================
from app.agents.base_agent import BaseAgent
from app.graph.state import SongWritingState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal
import json

# --- Pydantic Model for Structured Output (MUST match API model) ---
class LyricLine(BaseModel):
    """Defines the required output structure for each lyric line."""
    line: str = Field(..., description="The text of the lyric line.")
    source: Literal["human", "machine"] = Field(..., description="The origin of the line.")
    section: str = Field(..., description="Song section (e.g., '[verse 1]', '[chorus]').")
# --- End Pydantic Model ---


class CollaboratorAgent(BaseAgent):
    
    def __init__(self):
        super().__init__(agent_name="Collaborator", task_type="creative", use_tools=False, temperature=0.9)
        # Override for satirical escalation
        self.llm = ChatOllama(
            model="llama3.1:8b",
            base_url="http://host.docker.internal:11434",
            temperature=0.9
        )
        self.json_parser = JsonOutputParser(pydantic_object=List[LyricLine])

    def _prepare_draft_input(self, draft_lyrics_str: str) -> List[Dict[str, str]]:
        """Converts the raw string draft_lyrics from the initial state into structured 'human' lines."""
        if not draft_lyrics_str or draft_lyrics_str.lower() in ("none (initial draft)", "none"):
            return []
            
        # If the lyrics are already structured JSON (from a previous revision), return them.
        try:
            parsed_lyrics = json.loads(draft_lyrics_str)
            if isinstance(parsed_lyrics, list) and all('line' in item for item in parsed_lyrics):
                return parsed_lyrics
        except:
            pass # Not structured JSON, proceed to treat as raw human input.

        lines = [line.strip() for line in draft_lyrics_str.split('\n') if line.strip()]
        
        # Structure the raw human-provided lines for the initial prompt
        structured_human_lines = [
            LyricLine(line=line, source="human", section="[verse 1]").model_dump()
            for line in lines
        ]
        return structured_human_lines

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Implements the core logic for drafting and revising lyrics."""
        
        all_feedback = state.get('feedback', []) + state.get('critic_suggestions', [])
        feedback_str = "\n- " + "\n- ".join(all_feedback) if all_feedback else "No feedback provided yet."

        # 1. Prepare structured human/draft lines for the prompt
        structured_draft = self._prepare_draft_input(state['draft_lyrics'])
        structured_draft_json = json.dumps(structured_draft, indent=2)

        system_prompt = self._get_prompt_template(self.system_prompt_key)
        human_prompt_template = self._get_prompt_template(self.human_prompt_key)
        
        human_prompt = human_prompt_template.format(
            revision_number=state['revision_number'] + 1,
            inspiration=state['inspiration'],
            original_facts="\n".join(state['original_facts']),
            # Pass the structured lines for the agent to include/preserve
            human_lines_json=structured_draft_json, 
            feedback_and_suggestions=feedback_str
        )

        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ]) | self.llm | self.json_parser # Force JSON output
        
        try:
            # Invoke chain, which returns a List[Dict]
            new_lyrics_list = chain.invoke({})

            # Store the structured list as a JSON string in the state
            new_lyrics_str = json.dumps(new_lyrics_list) 
        except Exception as e:
            print(f"!!! Collaborator JSON parsing failed: {e} !!!")
            new_lyrics_str = state['draft_lyrics'] # Revert to last known good draft
            if not new_lyrics_str: 
                new_lyrics_str = f"Drafting/Revision failed (JSON error): {str(e)}"

        # Clear iteration-specific state keys upon revision start
        return {
            "draft_lyrics": new_lyrics_str, # The structured JSON string
            "revision_number": state['revision_number'] + 1,
            "feedback": [],
            "critic_suggestions": [],
            "critic_scores": {},
            "qa_status": False,
        }