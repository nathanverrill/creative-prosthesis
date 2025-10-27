# app/graph/workflow.py

from langgraph.graph import StateGraph, END
from typing import Dict, Any

from app.agents.researcher import ResearcherAgent
from app.agents.collaborator import CollaboratorAgent
from app.agents.brainstorm import YesAndAgent, NoButAgent, NonSequiturAgent
from app.agents.researcher import fact_check_node
from app.agents.critics import CriticsAgent
from app.graph.state import SongWritingState

def build_workflow():
    workflow = StateGraph(SongWritingState)
    
    agent_researcher = ResearcherAgent()
    agent_collaborator = CollaboratorAgent()
    agent_fact_check = fact_check_node
    agent_critics = CriticsAgent()
    
    # Instantiate brainstorm agents
    agent_yes_and = YesAndAgent()
    agent_no_but = NoButAgent()
    agent_non_sequitur = NonSequiturAgent()
    
    # Add all nodes
    workflow.add_node("researcher", agent_researcher)
    workflow.add_node("collaborator", agent_collaborator)
    workflow.add_node("yes_and", agent_yes_and)
    workflow.add_node("no_but", agent_no_but)
    workflow.add_node("non_sequitur", agent_non_sequitur)
    workflow.add_node("fact_check", agent_fact_check)
    workflow.add_node("critics", agent_critics)
    
    # Aggregator node to collect parallel feedback
    def aggregate_feedback(state: SongWritingState) -> Dict[str, Any]:
        """Collect feedback from parallel brainstorm agents."""
        feedback = state.get("feedback", [])
        print(f"[AGGREGATE] Collected {len(feedback)} feedback items")
        # Optional: Sort or prioritize (e.g., positives first)
        # state["feedback"] = sorted(feedback, key=lambda f: 1 if 'POSITIVE' in f else 0, reverse=True)
        return {}  # State already updated by parallel nodes
    
    workflow.add_node("aggregate_feedback", aggregate_feedback)
    
    # Sequential edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "collaborator")
    
    # Parallel edges: all three brainstorm agents run in parallel
    workflow.add_edge("collaborator", "yes_and")
    workflow.add_edge("collaborator", "no_but")
    workflow.add_edge("collaborator", "non_sequitur")
    
    # All parallel branches converge to aggregator
    workflow.add_edge("yes_and", "aggregate_feedback")
    workflow.add_edge("no_but", "aggregate_feedback")
    workflow.add_edge("non_sequitur", "aggregate_feedback")
    
    # Continue sequential flow
    workflow.add_edge("aggregate_feedback", "fact_check")
    workflow.add_edge("fact_check", "critics")
    
    def router(state: SongWritingState) -> str:
        thresholds = state.get("thresholds", {})
        scores = state.get("critic_scores", {})
        qa_status = state.get("qa_status", False)
        current_revision = state.get("revision_number", 0)
        
        creativity_thresh = thresholds.get("creativity", 0.5)
        freshness_thresh = thresholds.get("freshness", 0.5)
        humor_thresh = thresholds.get("humor", 0.4)
        
        # Enhanced logging: Write to file or console for tracing
        print(f"[ROUTER DEBUG] Revision: {current_revision}, Scores: {scores}, QA: {qa_status}")
        
        if current_revision >= 5:
            print("[ROUTER] Max revisions hit: Forcing release.")
            return "release"
        
        if (scores.get("creativity", 0) >= creativity_thresh and
            scores.get("freshness", 0) >= freshness_thresh and
            scores.get("humor", 0) >= humor_thresh and
            qa_status):
            print("[ROUTER] Thresholds met: Releasing.")
            return "release"
        else:
            print(f"[ROUTER] Thresholds not met: Revising.")
            return "revise"

    workflow.add_conditional_edges(
        "critics",
        router,
        {"release": END, "revise": "collaborator"}
    )
    
    return workflow.compile()

song_writer_app = build_workflow()