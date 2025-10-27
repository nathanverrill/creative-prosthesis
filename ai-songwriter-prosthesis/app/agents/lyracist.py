from app.graph.state import SongWritingState, LyricLine
from app.utils.prompt_manager import PromptManager
from app.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent
from pydantic import BaseModel, Field
from typing import List

from app.tools.search_tool import SearchTool
from app.tools.rhyme_tool import RhymeTool
from app.tools.lyrics_parser_tool import LyricsSummaryTool

llm = get_llm("lyracist_model")
prompt_manager = PromptManager()

class LyricLineList(BaseModel):
    """A list of lyric lines with provenance."""
    lyrics: List[LyricLine] = Field(description="The complete list of lyric lines for the song.")

async def lyracist_node(state: SongWritingState):
    """
    The Lyracist node. Drafts or revises lyrics using its tools.
    This is an async node.
    """
    print("---LYRACIST: RUNNING (ASYNC)---")
    
    version = state.get("draft_version", 0) + 1
    
    tools = [
        SearchTool(),
        RhymeTool(),
        LyricsSummaryTool(current_lyrics=state.get("draft_lyrics", []))
    ]
    
    is_drafting = not state.get("draft_lyrics", [])
    if is_drafting:
        print(f"---LYRACIST: DRAFTING (V{version})---")
        prompt_template = prompt_manager.get_prompt("lyracist", "draft")
    else:
        print(f"---LYRACIST: REVISING (V{version})---")
        prompt_template = prompt_manager.get_prompt("lyracist", "revise")

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_manager.get_prompt("lyracist", "system")),
        ("human", prompt_template)
    ])
    
    llm_with_tools = llm.with_structured_output(LyricLineList)
    
    agent = create_tool_calling_agent(llm_with_tools, tools, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        handle_parsing_errors=True
    )

    input_data = {
        "topic": state["topic"],
        "plan": state["creative_plan"],
        "structure": str(state.get("song_structure")),
        "lyrics": str(state.get("draft_lyrics", [])), 
        "feedback": str(state.get("critic_suggestions", [])),
        "version": version,
    }

    response = await agent_executor.ainvoke(input_data)
    
    structured_output: LyricLineList = response.get("output")
    
    if structured_output and hasattr(structured_output, 'lyrics'):
        new_lyrics = structured_output.lyrics
    else:
        print("---LYRACIST: ERROR: Failed to get structured output. Reverting.---")
        new_lyrics = state.get("draft_lyrics", [])
    
    print("---LYRACIST: DRAFT/REVISION COMPLETE---")

    return {
        "draft_lyrics": new_lyrics,
        "draft_version": version,
        "history": state.get("history", []) + [f"Lyracist created V{version}."]
    }