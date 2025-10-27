# app/graph/workflow.py

from langgraph.graph import StateGraph, END
from typing import Dict, Any
import ray

from app.agents.researcher import ResearcherAgent
from app.agents.collaborator import CollaboratorAgent
from app.agents.brainstorm import YesAndAgent, NoButAgent, NonSequiturAgent
from app.agents.researcher import fact_check_node
from app.agents.critics import CriticsAgent
from app.graph.state import SongWritingState

# Ray remote FUNCTIONS (not actors) for stateless parallel execution
@ray.remote
def run_yes_and(state: SongWritingState) -> Dict[str, Any]:
    """Remote function wrapper for YesAndAgent."""
    agent = YesAndAgent()
    return agent(state)

@ray.remote
def run_no_but(state: SongWritingState) -> Dict[str, Any]:
    """Remote function wrapper for NoButAgent."""
    agent = NoButAgent()
    return agent(state)

@ray.remote
def run_non_sequitur(state: SongWritingState) -> Dict[str, Any]:
    """Remote function wrapper for NonSequiturAgent."""
    agent = NonSequiturAgent()
    return agent(state)

def build_workflow():
    workflow = StateGraph(SongWritingState)
    
    # Instantiate agents (not Ray actors)
    agent_researcher = ResearcherAgent()
    agent_collaborator = CollaboratorAgent()
    agent_fact_check = fact_check_node
    agent_critics = CriticsAgent()
    
    # Add nodes
    workflow.add_node("researcher", agent_researcher)
    workflow.add_node("collaborator", agent_collaborator)
    workflow.add_node("fact_check", agent_fact_check)
    workflow.add_node("critics", agent_critics)
    
    # Parallel brainstorm node using Ray tasks
    def parallel_brainstorm(state: SongWritingState) -> Dict[str, Any]:
        """Execute three brainstorm agents in parallel using Ray."""
        try:
            # Launch all three as remote tasks
            yes_ref = run_yes_and.remote(state)
            no_ref = run_no_but.remote(state)
            ns_ref = run_non_sequitur.remote(state)
            
            # Wait for all results with timeout
            yes_out, no_out, ns_out = ray.get([yes_ref, no_ref, ns_ref], timeout=60.0)
            
            print("[PARALLEL_BRAINSTORM] Ray parallel execution completed.")
            
        except ray.exceptions.RayTaskError as e:
            print(f"[PARALLEL_BRAINSTORM] Ray task error: {e}—falling back to sequential.")
            yes_out = YesAndAgent()(state)
            no_out = NoButAgent()(state)
            ns_out = NonSequiturAgent()(state)
            
        except Exception as e:
            print(f"[PARALLEL_BRAINSTORM] Unexpected error: {e}—falling back to sequential.")
            yes_out = YesAndAgent()(state)
            no_out = NoButAgent()(state)
            ns_out = NonSequiturAgent()(state)
        
        # Aggregate feedback from all three agents
        aggregated_feedback = (
            yes_out.get("feedback", []) +
            no_out.get("feedback", []) +
            ns_out.get("feedback", [])
        )
        
        return {"feedback": aggregated_feedback}
    
    workflow.add_node("parallel_brainstorm", parallel_brainstorm)
    
    # Edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "collaborator")
    workflow.add_edge("collaborator", "parallel_brainstorm")
    workflow.add_edge("parallel_brainstorm", "fact_check")
    workflow.add_edge("fact_check", "critics")
    
    def router(state: SongWritingState) -> str:
        thresholds = state.get("thresholds", {})
        scores = state.get("critic_scores", {})
        qa_status = state.get("qa_status", False)
        current_revision = state.get("revision_number", 0)
        
        creativity_thresh = thresholds.get("creativity", 0.5)
        freshness_thresh = thresholds.get("freshness", 0.5)
        humor_thresh = thresholds.get("humor", 0.4)
        
        print(f"[ROUTER DEBUG] Revision: {current_revision}, Scores: {scores}, QA: {qa_status}, Thresholds: {thresholds}")
        
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

# Compile on import
song_writer_app = build_workflow()