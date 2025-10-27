# app/tools/lyrics_parser_tool.py
#
# A stateful tool for the Lyracist agent to get a clean
# text summary of the current lyrics, stripped of metadata.

from pydantic import BaseModel
from langchain.tools import BaseTool
from typing import Type, List, Dict, Any

# Define the LyricLine structure so the tool understands it
# This should match app/graph/state.py
try:
    from app.graph.state import LyricLine
except ImportError:
    # Fallback definition for portability
    LyricLine = Dict[str, Any]

class LyricsSummaryTool(BaseTool):
    """
    A tool to summarize the current lyric state.
    It takes NO input from the LLM.
    It returns a plain text version of the current draft lyrics,
    formatted with section headers.
    """
    name: str = "lyrics_summary_tool"
    description: str = (
        "Returns a plain text version of the current draft lyrics, "
        "stripped of all provenance metadata. Call this with no arguments "
        "to get a clean view of the song so far."
    )
    
    # This tool is stateful. The current lyrics are passed in
    # during its initialization inside the agent node.
    current_lyrics: List[LyricLine] = []

    # This tool takes no arguments from the LLM
    args_schema: Type[BaseModel] = None

    def _run(self) -> str:
        """Use the tool."""
        if not self.current_lyrics:
            return "No lyrics have been written yet."
        
        output = ""
        current_section = ""
        for line in self.current_lyrics:
            # Check if the section has changed
            section = line.get("section", "Unknown Section")
            if section != current_section:
                current_section = section
                output += f"\n[{current_section}]\n"
            
            # Add the lyric line
            output += f"{line.get('line', '')}\n"
        
        return output.strip()

    async def _arun(self) -> str:
        """Use the tool asynchronously."""
        # This operation is fast and not I/O bound,
        # so we can just call the sync method.
        return self._run()