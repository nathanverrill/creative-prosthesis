# app/tools/search_tool.py
#
# Wraps the SerpAPIWrapper as a formal LangChain tool for agent use.

import os
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_community.utilities import SerpAPIWrapper
from typing import Type

class SearchToolInput(BaseModel):
    """Input schema for the SearchTool."""
    query: str = Field(description="The search query to find information.")

class SearchTool(BaseTool):
    """
    A tool for performing web searches and retrieving factual information.
    Wraps the SerpAPIWrapper.
    """
    name: str = "web_search_tool"
    description: str = (
        "Useful for searching the internet for factual information, "
        "current events, or specific details."
    )
    args_schema: Type[BaseModel] = SearchToolInput
    
    # Initialize the SerpAPIWrapper
    # It's better to load the API key from environment variables
    # configured elsewhere (e.g., in main.py or via app_settings)
    _search_wrapper: SerpAPIWrapper = Field(
        default_factory=lambda: SerpAPIWrapper(
            serpapi_api_key=os.getenv("SERPAPI_API_KEY")
        )
    )

    def _run(self, query: str) -> str:
        """Use the tool."""
        try:
            return self._search_wrapper.run(query)
        except Exception as e:
            return f"Error during search: {e}"

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        try:
            # Note: SerpAPIWrapper may not have a native async run method.
            # If it doesn't, use asyncio.to_thread
            # For this example, we assume run is blocking and wrap it.
            import asyncio
            return await asyncio.to_thread(self._run, query)
        except Exception as e:
            return f"Error during async search: {e}"