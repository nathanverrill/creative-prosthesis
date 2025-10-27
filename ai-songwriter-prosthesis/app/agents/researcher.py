# ==============================================================================
# --- app/agents/researcher.py (Including fact_check_node) ---
# ==============================================================================
from app.agents.base_agent import BaseAgent
from app.graph.state import SongWritingState
from app.utils.llm import search_tool 
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from typing import Dict, Any
import json

# --- Helper Function (Copied for local use) ---
def extract_plain_lyrics_researcher(draft_lyrics_json_str: str) -> str:
    """Extracts a simple, readable string from the structured lyrics JSON."""
    if not draft_lyrics_json_str:
        return "No current draft."
    try:
        lyrics_list = json.loads(draft_lyrics_json_str)
        return "\n".join([item.get('line', '') for item in lyrics_list if isinstance(item, dict)])
    except:
        return draft_lyrics_json_str
# --- End Helper Function ---


class ResearcherAgent(BaseAgent):
    
    def __init__(self):
        super().__init__(agent_name="Researcher", task_type="research", use_tools=True, temperature=0.2) 
        # Override for factual precision
        self.llm = ChatOllama(
            model="mistral-nemo:12b",
            base_url="http://host.docker.internal:11434",
            temperature=0.2
        )

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Gathers initial facts using the search tool."""
        
        # We manually invoke the tool for simplicity in this node
        search_query = f"Key facts and context for song about: {state['inspiration']}"
        # Assuming search_tool has a run method that accepts num_results
        facts_result = search_tool.run(search_query, num_results=5) 
        
        # The result might be a long string; convert to a list for the state
        # Truncate for state brevity
        facts_list = [f"Source: SERP, Result: {facts_result[:300]}..."] if facts_result else ["No facts found."]

        # Initialize feedback list here, as this is the entry node
        return {"original_facts": facts_list, "feedback": []}

# Fact check node
def fact_check_node(state: SongWritingState) -> Dict[str, Any]:
    """Node for AI_Researcher to fact-check the current draft."""
    
    # Create factual LLM for check
    llm = ChatOllama(
        model="mistral-nemo:12b",
        base_url="http://host.docker.internal:11434",
        temperature=0.1
    )
    
    # --- NEW: Convert structured JSON to plain text for prompt ---
    plain_lyrics = extract_plain_lyrics_researcher(state['draft_lyrics'])
    
    # Get the specific fact-check prompt
    from app.utils.prompt_manager import prompt_manager
    system_prompt = prompt_manager.get_prompt("fact_check_system")
    human_prompt = prompt_manager.get_prompt("fact_check_human").format(
        draft_lyrics=plain_lyrics, # Use plain text
        original_facts="\n".join(state['original_facts'])
    )
    
    # Create a simple chain: messages -> LLM -> extract content
    from langchain_core.prompts import ChatPromptTemplate
    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ]) | llm | (lambda msg: msg.content)
    
    try:
        response_content = chain.invoke({})
    except Exception as e:
        response_content = f"Fact-check failed: {str(e)}"
    
    # Update both the specific fact check list AND the general feedback list
    return {
        # fact_checked_feedback is not in the official state, but good for local logging/debug
        # "fact_checked_feedback": [response_content], 
        "feedback": state['feedback'] + [response_content],
        "qa_status": "pass" in response_content.lower(),  # Simple heuristic
    }