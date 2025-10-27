# app/utils/prompt_manager.py
#
# Updated to load prompts from config/prompts/prompts.yaml.

import yaml
from pathlib import Path
from typing import Dict, Any

class PromptManager:
    """
    Loads and manages prompt templates from external YAML files.
    """
    
    def __init__(self, config_dir: Path = Path("config")):
        self.prompts_path = config_dir / "prompts" / "prompts.yaml"
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Any]:
        """
        Loads the prompts.yaml file.
        """
        if not self.prompts_path.exists():
            # Fallback for when CWD is not project root
            self.prompts_path = Path(__file__).parent.parent.parent / "config" / "prompts" / "prompts.yaml"
            if not self.prompts_path.exists():
                print(f"Error: Could not find prompts file at {self.prompts_path}")
                return {}

        try:
            with open(self.prompts_path, 'r', encoding='utf-8') as f:
                prompts_data = yaml.safe_load(f)
            print("Successfully loaded prompts from prompts.yaml")
            return prompts_data
        except Exception as e:
            print(f"Error loading prompts from {self.prompts_path}: {e}")
            return {}

    def get_prompt(self, agent: str, template: str) -> str:
        """
        Retrieves a specific prompt template.
        
        Args:
            agent: The top-level key (e.g., "producer", "lyracist").
            template: The second-level key (e.g., "system", "draft").
            
        Returns:
            The prompt template string.
        """
        try:
            return self.prompts[agent][template]
        except KeyError:
            print(f"Error: Prompt not found for {agent}.{template}")
            return f"PROMPT_NOT_FOUND: {agent}.{template}"

# Example usage (if run directly)
if __name__ == "__main__":
    # Assumes running from project root or 'app/utils'
    manager = PromptManager()
    
    producer_system = manager.get_prompt("producer", "system")
    print("--- Producer System Prompt ---")
    print(producer_system)
    
    lyracist_draft = manager.get_prompt("lyracist", "draft")
    print("\n--- Lyracist Draft Prompt ---")
    print(lyracist_draft)