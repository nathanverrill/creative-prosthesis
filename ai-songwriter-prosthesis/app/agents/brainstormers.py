from app.graph.state import SongWritingState
from app.utils.prompt_manager import PromptManager
from app.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from typing import List
import asyncio

llm = get_llm("brainstormer_model")
prompt_manager = PromptManager()

async def run_brainstormer(
    prompt_key: str, 
    lyrics_str: str
) -> str:
    """Helper to run a single brainstormer LLM call."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_manager.get_prompt("brainstormers", prompt_key)),
        ("human", "{lyrics}")
    ])
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"lyrics": lyrics_str})
        return f"[{prompt_key.upper()}]: {response.content}"
    except Exception as e:
        return f"[{prompt_key.upper()}]: Error - {e}"

async def brainstormer_node(state: SongWritingState):
    """
    Runs all brainstormers in parallel and collects feedback.
    This is an async node.
    """
    print("---BRAINSTORMERS: RUNNING IN PARALLEL (ASYNC)---")
    
    lyrics_str = "\n".join([l['line'] for l in state.get('draft_lyrics', [])])
    if not lyrics_str:
        return {
            "brainstorm_feedback": ["No lyrics to brainstorm on."],
            "history": state.get("history", []) + ["Brainstormers skipped (no lyrics)."]
        }

    tasks = [
        run_brainstormer("yes_and", lyrics_str),
        run_brainstormer("no_but", lyrics_str),
        run_brainstormer("non_sequitur", lyrics_str),
    ]
    
    feedback = await asyncio.gather(*tasks)
        
    print("---BRAINSTORMERS: FEEDBACK GATHERED---")

    return {
        "brainstorm_feedback": feedback,
        "history": state.get("history", []) + ["Brainstormers provided feedback."]
    }