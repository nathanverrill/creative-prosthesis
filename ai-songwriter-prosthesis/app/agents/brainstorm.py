# ==============================================================================
# --- app/agents/brainstorm.py ---
# ==============================================================================
from app.agents.base_agent import BaseAgent
from app.graph.state import SongWritingState
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
import json

# --- Helper Function to Extract Plain Lyrics ---
def extract_plain_lyrics(draft_lyrics_json_str: str) -> str:
    """Extracts a simple, readable string from the structured lyrics JSON."""
    if not draft_lyrics_json_str:
        return "No current draft."
    try:
        lyrics_list = json.loads(draft_lyrics_json_str)
        # Join only the 'line' field
        return "\n".join([item.get('line', '') for item in lyrics_list if isinstance(item, dict)])
    except:
        # Fallback if it's not structured JSON
        return draft_lyrics_json_str
# --- End Helper Function ---


# --- 1. AI_YesAnd Agent ---
class YesAndAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="YesAnd", task_type="creative", use_tools=False, temperature=0.8)
        # Override for creative amp-up
        self.llm = ChatOllama(
            model="llama3.1:8b",
            base_url="http://host.docker.internal:11434",
            temperature=0.8
        )

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Provides positive brainstorming feedback."""
        
        plain_lyrics = extract_plain_lyrics(state['draft_lyrics'])
        
        system_prompt = self._get_prompt_template(self.system_prompt_key)
        human_prompt = self._get_prompt_template(self.human_prompt_key).format(
            draft_lyrics=plain_lyrics
        )
        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ]) | self.llm
        
        try:
            response = chain.invoke({})
            new_feedback = f"POSITIVE: {response.content}"
            return {"feedback": [new_feedback]}
            
        except Exception as e:
            error_feedback = f"POSITIVE: Feedback generation failed - {str(e)}"
            return {"feedback": [error_feedback]}

# --- 2. AI_NoBut Agent ---
class NoButAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="NoBut", task_type="research", use_tools=False, temperature=0.6)
        # Override for balanced critique (factual base)
        self.llm = ChatOllama(
            model="mistral-nemo:12b",
            base_url="http://host.docker.internal:11434",
            temperature=0.6
        )

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Provides critical, actionable feedback."""
        
        plain_lyrics = extract_plain_lyrics(state['draft_lyrics'])

        system_prompt = self._get_prompt_template(self.system_prompt_key)
        human_prompt = self._get_prompt_template(self.human_prompt_key).format(
            draft_lyrics=plain_lyrics
        )
        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ]) | self.llm
        
        try:
            response = chain.invoke({})
            new_feedback = f"CRITICAL: {response.content}"
            return {"feedback": [new_feedback]}
            
        except Exception as e:
            error_feedback = f"CRITICAL: Feedback generation failed - {str(e)}"
            return {"feedback": [error_feedback]}

# --- 3. AI_NonSequitur Agent (Lateral Thinking) ---
class NonSequiturAgent(BaseAgent):
    
    def __init__(self):
        super().__init__(agent_name="NonSequitur", task_type="creative", use_tools=False, temperature=1.0)
        # Override for chaos via creativity
        self.llm = ChatOllama(
            model="llama3.1:8b",
            base_url="http://host.docker.internal:11434",
            temperature=1.0
        )

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Generates a random, unrelated input to spark lateral thinking."""
        
        plain_lyrics = extract_plain_lyrics(state['draft_lyrics'])
        
        system_prompt = self._get_prompt_template(self.system_prompt_key) 
        human_prompt = self._get_prompt_template(self.human_prompt_key).format(
            current_draft=plain_lyrics
        )
        
        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ]) | self.llm
        
        try:
            response = chain.invoke({})
            new_feedback = f"LATERAL INPUT (Random): {response.content}"
            return {"feedback": [new_feedback]}
            
        except Exception as e:
            error_feedback = f"LATERAL INPUT (Random): Generation failed - {str(e)}"
            return {"feedback": [error_feedback]}