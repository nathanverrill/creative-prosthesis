# app/tools/rhyme_tool.py
#
# Optional utility for rhyme/meter checking.

from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from typing import Type, List
import re

# In a real app, you might use a library like 'rhymes'
# pip install rhymes
# from rhymes import Rhymes

class RhymeCheckInput(BaseModel):
    """Input schema for the RhymeTool."""
    word: str = Field(description="The word to find rhymes for.")

class RhymeTool(BaseTool):
    """
    A tool to find rhymes for a given word.
    """
    name: str = "rhyme_finder_tool"
    description: str = "Finds a list of rhymes for a specific word."
    args_schema: Type[BaseModel] = RhymeCheckInput
    
    # Placeholder for a real rhyming engine
    _rhyme_engine = None 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self._rhyme_engine = Rhymes() # If using the 'rhymes' library

    def _run(self, word: str) -> List[str]:
        """Use the tool."""
        # Clean the word
        word = re.sub(r'[^\w\s]', '', word).strip().lower()
        if not word:
            return ["Invalid word."]

        try:
            # Placeholder logic
            # return self._rhyme_engine.rhyme(word)
            if word == "time":
                return ["rhyme", "crime", "lime", "prime", "climb"]
            if word == "world":
                return ["curled", "hurled", "twirled"]
            return [f"No rhymes found for '{word}' (placeholder)."]
        
        except Exception as e:
            return [f"Error finding rhymes: {e}"]

    async def _arun(self, word: str) -> List[str]:
        """Use the tool asynchronously."""
        import asyncio
        return await asyncio.to_thread(self._run, word)