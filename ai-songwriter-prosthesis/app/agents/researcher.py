from app.graph.state import SongWritingState
from app.utils.prompt_manager import PromptManager
from app.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent
from pydantic import BaseModel, Field
from typing import List

from app.tools.search_tool import SearchTool

llm = get_llm("researcher_model")
prompt_manager = PromptManager()

class FactList(BaseModel):
    """A list of facts found by the researcher."""
    facts: List[str] = Field(description="A list of 3-5 key facts summarizing the research findings.")

async def researcher_node(state: SongWritingState):
    """
    The Researcher node. Its sole job is to use the SearchTool
    to answer a query provided in the state. (Async)
    """
    print("---RESEARCHER: CONDUCTING RESEARCH (ASYNC)---")
    
    tools = [SearchTool()]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_manager.get_prompt("researcher", "system")),
        ("human", prompt_manager.get_prompt("researcher", "query"))
    ])
    
    llm_with_facts = llm.with_structured_output(FactList)
    
    agent = create_tool_calling_agent(llm_with_facts, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        handle_parsing_errors=True
    )

    query = state.get("research_query", state.get("topic", "No query provided"))
    
    if query == "No query provided":
         print("---RESEARCHER: SKIPPED (NO QUERY)---")
         return {
             "history": state.get("history", []) + ["Researcher skipped (no query)."]
         }

    print(f"---RESEARCHER: RUNNING QUERY: {query}---")

    response = await agent_executor.ainvoke({"query": query})
    
    structured_output: FactList = response.get("output")
    
    if structured_output and hasattr(structured_output, 'facts'):
        new_facts = structured_output.facts
    else:
        print("---RESEARCHER: ERROR: Failed to get structured facts.---")
        new_facts = ["Researcher failed to extract structured facts."]

    print("---RESEARCHER: RESEARCH COMPLETE---")

    return {
        "research_facts": state.get("research_facts", []) + new_facts,
        "research_query": None,
        "history": state.get("history", []) + ["Researcher found facts."]
    }