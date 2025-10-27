# app/agents/researcher.py

from app.agents.base_agent import BaseAgent
from app.graph.state import SongWritingState
from app.utils.llm import search_tool  # Directly use the tool
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any

class ResearcherAgent(BaseAgent):
    
    def __init__(self):
        super().__init__(agent_name="Researcher", use_tools=True, temperature=0.2) 

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Gathers initial facts using the search tool."""
        
        # We manually invoke the tool for simplicity in this node
        search_query = f"Key facts and context for song about: {state['inspiration']}"
        facts_result = search_tool.run(search_query, num_results=5)  # Pass num_results here
        
        # The result might be a long string; convert to a list for the state (truncate to 300 chars per fact for brevity)
        facts_list = [f"Source: SERP, Result: {facts_result[:300]}..."] if facts_result else ["No facts found."]

        # Initialize feedback list here, as this is the entry node
        return {"original_facts": facts_list, "feedback": []}

# Fact check node remains unchanged (no tool call there)
def fact_check_node(state: SongWritingState) -> Dict[str, Any]:
    """Node for AI_Researcher to fact-check the current draft."""
    
    # Initialize a temporary agent for fact check logic
    checker = ResearcherAgent()
    
    # Get the specific fact-check prompt
    system_prompt = checker._get_prompt_template("fact_check_system")
    human_prompt = checker._get_prompt_template("fact_check_human").format(
        draft_lyrics=state['draft_lyrics'],
        original_facts=state['original_facts']
    )
    
    # Create a simple chain: messages -> LLM -> extract content
    chain = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ]) | checker.llm | (lambda msg: msg.content)
    
    try:
        response_content = chain.invoke({})
    except Exception as e:
        response_content = f"Fact-check failed: {str(e)}"
    
    # Update both the specific fact check list AND the general feedback list
    return {
        "fact_checked_feedback": [response_content], 
        "feedback": state['feedback'] + [response_content],
        "qa_status": "pass" in response_content.lower(),  # Simple heuristic; refine with structured output if needed
    }