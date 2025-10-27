from app.graph.state import SongWritingState
from app.utils.prompt_manager import PromptManager
from app.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
import json

llm = get_llm("producer_model")
prompt_manager = PromptManager()

async def producer_node(state: SongWritingState):
    """
    The Producer node. Analyzes the state (and critic scores) 
    to decide the next step.
    """
    
    if not state.get("creative_plan"):
        print("---PRODUCER: CREATING INITIAL PLAN---")
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_manager.get_prompt("producer", "system_plan")),
            ("human", prompt_manager.get_prompt("producer", "plan"))
        ])
        
        chain = prompt | llm
        plan_output = await chain.ainvoke({"topic": state["topic"]})
        
        # TODO: Add parsing logic for plan_output content
        
        return {
            "creative_plan": f"Mocked plan based on: {plan_output.content[:50]}...",
            "song_structure": ["Verse 1", "Chorus", "Verse 2"],
            "history": state.get("history", []) + ["Producer created plan."],
            "next_step": "LYRACIST"
        }

    print("---PRODUCER: ROUTING (POST-CRITIC)---")
    
    scores = state.get("critic_scores", {})
    suggestions = state.get("critic_suggestions", [])
    qa_status = state.get("qa_status", False)
    
    critic_summary = (
        f"Critic Scores (0.0-1.0): {json.dumps(scores, indent=2)}\n"
        f"Fact Check Passed: {qa_status}\n"
        f"Critic's Suggestions: \n- {'\n- '.join(suggestions)}"
    )
    print(f"Producer reviewing:\n{critic_summary}")

    avg_score = sum(scores.values()) / len(scores) if scores else 0
    
    if avg_score >= 0.9 and qa_status:
        print("---PRODUCER: SONG IS COMPLETE (CRITIC SCORES HIGH)---")
        return {"next_step": "TERMINATE"}
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_manager.get_prompt("producer", "system_router")),
        ("human", prompt_manager.get_prompt("producer", "router"))
    ])
    chain = prompt | llm
    
    router_decision = await chain.ainvoke({
        "topic": state["topic"],
        "plan": state["creative_plan"],
        "critic_summary": critic_summary,
        "history": "\n".join(state.get("history", []))
    })
    
    decision_content = router_decision.content.upper()
    next_step = "LYRACIST"
    if "TERMINATE" in decision_content:
        next_step = "TERMINATE"
    elif "RESEARCHER" in decision_content:
        next_step = "RESEARCHER"
    elif "BRAINSTORMERS" in decision_content:
        next_step = "BRAINSTORMERS"
    
    print(f"---PRODUCER: NEXT STEP IS {next_step}---")

    return {
        "history": state.get("history", []) + [f"Producer routed to {next_step}."],
        "next_step": next_step,
        "research_query": None
    }