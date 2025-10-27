# app/agents/base_agent.py

from typing import Dict, Any
from app.graph.state import SongWritingState
from app.utils.llm import OLLAMA_BASE_URL, search_tool  # Import URL and tool
from app.utils.prompt_manager import prompt_manager
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama  # Import here for per-agent creation

# Phoenix OTel instrumentation (global, runs on import—traces all models)
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

tracer_provider = register()  # Configures Phoenix as OTel exporter
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# Model mapping for dynamic loading (creative vs. research tasks) - FIXED: Swapped for better specialization
MODEL_MAP = {
    "creative": "llama3.1:8b",      # High creativity/humor for drafting/brainstorming
    "research": "mistral-nemo:12b"  # Precise, low-hallucination for facts/critique
}

class BaseAgent:
    """Foundational class for all agents to enforce node signature and centralize config."""
    
    def __init__(self, agent_name: str, task_type: str = "creative", use_tools: bool = False, temperature: float = 0.7):
        self.agent_name = agent_name
        
        # Select model based on task_type (loads dynamically in Ollama)
        model_name = MODEL_MAP.get(task_type, MODEL_MAP["creative"])  # Default to creative
        
        # Create model fresh with temperature in constructor (puts it in options; no bind/kwarg leak)
        if use_tools:
            # Research: Low temp for factual (overrides task_type if needed)
            self.llm = ChatOllama(
                model=model_name,
                base_url=OLLAMA_BASE_URL,
                temperature=0.2
            )
        else:
            # Creative: Agent-specific temp
            self.llm = ChatOllama(
                model=model_name,
                base_url=OLLAMA_BASE_URL,
                temperature=temperature  # e.g., 0.9 for collaborator, 0.8 for YesAnd
            )
            
        self.system_prompt_key = f"{self.agent_name.lower()}_system"
        self.human_prompt_key = f"{self.agent_name.lower()}_human"

    def _get_prompt_template(self, key: str) -> str:
        """Retrieves prompt dynamically and handles potential missing keys."""
        return prompt_manager.get_prompt(key)

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """The mandatory LangGraph Node signature method."""
        raise NotImplementedError(f"Agent {self.agent_name} must implement the __call__ method.")