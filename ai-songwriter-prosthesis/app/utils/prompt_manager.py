# app/utils/prompt_manager.py

from typing import Dict
from app.prompts.song_prompts import PROMPTS  # Import all prompts

class PromptManager:
    """Singleton for loading and retrieving prompts by key."""
    
    _prompts: Dict[str, str] = {}
    
    def __init__(self):
        if not self._prompts:
            self._prompts = PROMPTS  # Load on init
    
    def get_prompt(self, key: str) -> str:
        """Get prompt by key; raise if missing."""
        if key not in self._prompts:
            raise KeyError(f"Prompt '{key}' not found. Available: {list(self._prompts.keys())}")
        return self._prompts[key]

# Global instance
prompt_manager = PromptManager()