# app/graph/workflow.py

from langgraph.graph import StateGraph, END
from typing import Dict, Any

# Import agent classes (adjust if you have instances in app/graph/agents.py)
from app.agents.researcher import ResearcherAgent
from app.agents.collaborator import CollaboratorAgent
from app.agents.brainstorm import YesAndAgent, NoButAgent, NonSequiturAgent
from app.agents.researcher import fact_check_node  # Standalone function node
from app.agents.critics import CriticsAgent
from app.graph.state import SongWritingState

def build_workflow():
    workflow = StateGraph(SongWritingState)
    
    # 1. Instantiate Agents (as nodes)
    agent_researcher = ResearcherAgent()
    agent_collaborator = CollaboratorAgent()
    agent_yes_and = YesAndAgent()
    agent_no_but = NoButAgent()
    agent_non_sequitur = NonSequiturAgent()
    agent_fact_check = fact_check_node  # Function directly as node
    agent_critics = CriticsAgent()
    
    # 2. Add Nodes
    workflow.add_node("researcher", agent_researcher)
    workflow.add_node("collaborator", agent_collaborator)
    workflow.add_node("yes_and", agent_yes_and)
    workflow.add_node("no_but", agent_no_but)
    workflow.add_node("non_sequitur", agent_non_sequitur)
    workflow.add_node("fact_check", agent_fact_check)
    workflow.add_node("critics", agent_critics)
    
    # 3. Set Edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "collaborator")  # Initial facts → draft
    workflow.add_edge("collaborator", "yes_and")     # Draft → start brainstorm
    workflow.add_edge("yes_and", "no_but")           # Chain brainstormers (accumulate feedback)
    workflow.add_edge("no_but", "non_sequitur")
    workflow.add_edge("non_sequitur", "fact_check")  # All feedback → fact-check current draft
    workflow.add_edge("fact_check", "critics")       # Fact-check → score
    
    # 4. Conditional Router (after critics) - Enhanced with logging & tighter guard
    def router(state: SongWritingState) -> str:
        thresholds = state.get("thresholds", {})  # User-provided, fallback to empty
        scores = state.get("critic_scores", {})
        qa_status = state.get("qa_status", False)
        current_revision = state.get("revision_number", 0)
        
        # Extract thresholds with defaults (looser for testing)
        creativity_thresh = thresholds.get("creativity", 0.5)  # Lowered default
        freshness_thresh = thresholds.get("freshness", 0.5)
        humor_thresh = thresholds.get("humor", 0.4)
        
        # Log for debug (visible in Docker logs)
        print(f"[ROUTER DEBUG] Revision: {current_revision}, Scores: {scores}, QA: {qa_status}, Thresholds: {thresholds}")
        
        # Tighter max revisions guard: Force release after 5 full cycles (prevents deep recursion)
        if current_revision >= 5:
            print("[ROUTER] Max revisions hit: Forcing release.")
            return "release"
        
        # Pass if all scores meet thresholds AND QA passes
        if (scores.get("creativity", 0) >= creativity_thresh and
            scores.get("freshness", 0) >= freshness_thresh and
            scores.get("humor", 0) >= humor_thresh and
            qa_status):
            print("[ROUTER] Thresholds met: Releasing.")
            return "release"
        else:
            print(f"[ROUTER] Thresholds not met: Revising (creativity={scores.get('creativity',0):.2f} < {creativity_thresh}).")
            return "revise"

    workflow.add_conditional_edges(
        "critics",
        router,
        {"release": END, "revise": "collaborator"}  # Loop back to revise (triggers new brainstorm)
    )
    
    # 5. Compile without recursion_limit (set per-invoke instead)
    return workflow.compile()

# Compile the graph on import
song_writer_app = build_workflow()