# app/agents/brainstorm.py

from app.agents.base_agent import BaseAgent
from app.graph.state import SongWritingState
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

# --- 1. AI_YesAnd Agent ---
class YesAndAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="YesAnd", use_tools=False, temperature=0.8)

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Provides positive brainstorming feedback."""
        system_prompt = self._get_prompt_template(self.system_prompt_key)
        human_prompt = self._get_prompt_template(self.human_prompt_key).format(
            draft_lyrics=state['draft_lyrics']
        )
        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ]) | self.llm
        try:
            response = chain.invoke({})
            return {"feedback": [f"POSITIVE: {response.content}"]}
        except Exception as e:
            return {"feedback": [f"POSITIVE: Feedback generation failed - {str(e)}"]}

# --- 2. AI_NoBut Agent ---
class NoButAgent(BaseAgent):
    def __init__(self):
        # Slightly lower temp for more structured, focused critique
        super().__init__(agent_name="NoBut", use_tools=False, temperature=0.6) 

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Provides critical, actionable feedback."""
        system_prompt = self._get_prompt_template(self.system_prompt_key)
        human_prompt = self._get_prompt_template(self.human_prompt_key).format(
            draft_lyrics=state['draft_lyrics']
        )
        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ]) | self.llm
        try:
            response = chain.invoke({})
            return {"feedback": [f"CRITICAL: {response.content}"]}
        except Exception as e:
            return {"feedback": [f"CRITICAL: Feedback generation failed - {str(e)}"]}

# --- 3. AI_NonSequitur Agent (Lateral Thinking) ---
class NonSequiturAgent(BaseAgent):
    
    def __init__(self):
        # Extremely high temperature (1.0) for maximum random disruption
        super().__init__(agent_name="NonSequitur", use_tools=False, temperature=1.0) 

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Generates a random, unrelated input to spark lateral thinking."""
        
        # NOTE: You must define 'nonsequitur_system' and 'nonsequitur_human' prompts
        system_prompt = self._get_prompt_template(self.system_prompt_key) 
        human_prompt = self._get_prompt_template(self.human_prompt_key).format(
            current_draft=state['draft_lyrics']
        )
        
        # Use a simple chain to generate one unrelated concept
        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ]) | self.llm
        
        try:
            response = chain.invoke({})
            # Label the output clearly so the Collaborator knows it's random
            non_sequitur_input = f"LATERAL INPUT (Random): {response.content}"
            return {"feedback": [non_sequitur_input]}  # Appended to the shared feedback list
        except Exception as e:
            return {"feedback": [f"LATERAL INPUT (Random): Generation failed - {str(e)}"]}