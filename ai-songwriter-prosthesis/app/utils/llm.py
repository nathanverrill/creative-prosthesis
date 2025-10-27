# app/utils/llm.py

# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_community.utilities import SerpAPIWrapper
# from app.config import GOOGLE_API_KEY, SERPAPI_API_KEY  # Assuming your structure

# # Creative model (default higher temp for drafting/brainstorm)
# creative_model = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=GOOGLE_API_KEY,
#     temperature=0.7
# )

# # Research model (lower temp for facts/checks)
# research_model = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0.2,
#     google_api_key=GOOGLE_API_KEY
# )

# # SERP search tool for facts (use .run(query, num_results=5) in agents)
# search_tool = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)  # No 'k' here

 # app/utils/llm.py
# app/utils/llm.py

# utils/llm.py
#
# Centralized factory for creating Ollama LLM instances.
# Reads configuration from app_settings.yaml.

import yaml
from pathlib import Path
from langchain_community.chat_models import ChatOllama
from typing import Literal, Dict, Any

# Define agent model types
AgentModelName = Literal[
    "producer_model",
    "lyracist_model",
    "brainstormer_model",
    "researcher_model",
    "critic_creative_model",
    "critic_factual_model",
    "critic_synthesizer_model"
]

# --- Config Loading ---

def _load_config() -> Dict[str, Any]:
    """Loads the app_settings.yaml file."""
    try:
        config_path = Path(__file__).parent.parent / "config" / "app_settings.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        if not config:
            raise FileNotFoundError("Config file is empty or missing.")
        return config
    except Exception as e:
        print(f"FATAL ERROR: Could not load config/app_settings.yaml. {e}")
        # Return a minimal structure to prevent crashes, though it will fail
        return {"llm_provider": {"base_url": ""}, "models": {}, "generation_config": {}}

# Load the config once when the module is imported
_CONFIG = _load_config()
_OLLAMA_BASE_URL = _CONFIG.get("llm_provider", {}).get("base_url")

# --- End Config Loading ---


def get_llm(model_name: AgentModelName, temperature: float = None) -> ChatOllama:
    """
    Fetches the correct, configured Ollama model for a specific agent.
    
    Args:
        model_name: The agent's model key (e.g., "producer_model").
        temperature: An optional override for temperature.
    
    Returns:
        A ChatOllama instance.
    """
    
    # 1. Determine the model string (e.g., "mistral-nemo:12b")
    # It might be a top-level model or a nested critic model
    if "critic" in model_name:
        model_key = model_name.replace("critic_", "") # e.g., "creative_model"
        model_str = _CONFIG["models"]["critic"].get(model_key)
    else:
        model_str = _CONFIG["models"].get(model_name)

    if not model_str:
        raise ValueError(f"No model string found in app_settings.yaml for '{model_name}'")

    # 2. Determine the temperature
    if temperature is None:
        # Check for agent-specific temperature
        if model_name == "lyracist_model":
            temp_key = "lyracist_temperature"
        elif model_name == "critic_creative_model":
            temp_key = "critic_creative_temp"
        elif model_name == "critic_factual_model":
            temp_key = "critic_factual_temp"
        else:
            temp_key = "temperature" # Default
        
        temperature = _CONFIG["generation_config"].get(temp_key, 0.7)

    # 3. Create and return the ChatOllama instance
    return ChatOllama(
        base_url=_OLLAMA_BASE_URL,
        model=model_str,
        temperature=temperature
    )

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    print(f"Loading config from base URL: {_OLLAMA_BASE_URL}")
    
    producer_llm = get_llm("producer_model")
    print(f"Producer LLM: {producer_llm.model} @ {producer_llm.temperature}")
    
    lyracist_llm = get_llm("lyracist_model")
    print(f"Lyracist LLM: {lyracist_llm.model} @ {lyracist_llm.temperature}")
    
    critic_llm = get_llm("critic_factual_model")
    print(f"Critic Factual LLM: {critic_llm.model} @ {critic_llm.temperature}")