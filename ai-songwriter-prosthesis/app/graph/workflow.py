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

# Ray integration for parallelization (add to requirements.txt: ray[default]==2.10.0)
import ray

# Optimized init: Match M1 Pro cores, size object store to ~6% RAM (2GB safe), suppress warnings
ray.init(
    ignore_reinit_error=True,
    num_cpus=10,  # Your M1 Pro total cores—auto-scales tasks
    object_store_memory=2000000000,  # 2GB for state/feedback sharing (avoids /tmp; ~6% of 32GB)
    # runtime_env={"env_vars": {"OMP_NUM_THREADS": "1"}}  # Optional: Pin threads per task (uncomment for finer control)
)

# Remote actor wrappers for brainstorm agents (optimized: 1 CPU each, concurrency=1 to avoid Ollama overload)
@ray.remote(num_cpus=1, max_concurrency=1)  # 1 core per actor; no overlap to prevent resource contention
class YesAndRemote(YesAndAgent):
    pass  # Inherits __init__ and __call__; Ray serializes state

@ray.remote(num_cpus=1, max_concurrency=1)
class NoButRemote(NoButAgent):
    pass

@ray.remote(num_cpus=1, max_concurrency=1)
class NonSequiturRemote(NonSequiturAgent):
    pass

def build_workflow():
    workflow = StateGraph(SongWritingState)
    
    # 1. Instantiate Agents (as nodes)
    agent_researcher = ResearcherAgent()
    agent_collaborator = CollaboratorAgent()
    # No individual nodes for brainstormers—use parallel composite below
    agent_fact_check = fact_check_node  # Function directly as node
    agent_critics = CriticsAgent()
    
    # 2. Add Nodes
    workflow.add_node("researcher", agent_researcher)
    workflow.add_node("collaborator", agent_collaborator)
    workflow.add_node("fact_check", agent_fact_check)
    workflow.add_node("critics", agent_critics)
    
    # 3. Parallel Brainstorm Node (Ray-powered: Runs YesAnd/NoBut/NonSequitur concurrently)
    def parallel_brainstorm(state: SongWritingState) -> Dict[str, Any]:
        """Parallel execution of brainstorm agents using Ray remotes."""
        # Create remote actors (one-time; reuse for efficiency)
        yes_actor = YesAndRemote.remote()
        no_actor = NoButRemote.remote()
        ns_actor = NonSequiturRemote.remote()
        
        # Submit parallel tasks (non-blocking)
        yes_ref = yes_actor.__call__.remote(state)
        no_ref = no_actor.__call__.remote(state)
        ns_ref = ns_actor.__call__.remote(state)
        
        # Wait for all with timeout (prevents hangs on slow Ollama; 30s ample for M1 Pro)
        try:
            yes_out, no_out, ns_out = ray.get([yes_ref, no_ref, ns_ref], timeout=30.0)
        except ray.exceptions.TimeoutError:
            print("[PARALLEL_BRAINSTORM] Timeout—falling back to sequential.")
            # Fallback: Run sequential (rare; for resilience)
            yes_out = YesAndAgent().__call__(state)
            no_out = NoButAgent().__call__(state)
            ns_out = NonSequiturAgent().__call__(state)
        
        # Aggregate feedback into state
        aggregated_feedback = (
            yes_out.get("feedback", []) +
            no_out.get("feedback", []) +
            ns_out.get("feedback", [])
        )
        
        # Return merged state update
        return {"feedback": aggregated_feedback}
    
    workflow.add_node("parallel_brainstorm", parallel_brainstorm)
    
    # 4. Set Edges (Replace chaining with single parallel node)
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "collaborator")  # Initial facts → draft
    workflow.add_edge("collaborator", "parallel_brainstorm")  # Draft → parallel brainstorm
    workflow.add_edge("parallel_brainstorm", "fact_check")  # Aggregated feedback → fact-check
    workflow.add_edge("fact_check", "critics")       # Fact-check → score
    
    # 5. Conditional Router (after critics) - Enhanced with logging & tighter guard
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
        {"release": END, "revise": "collaborator"}  # Loop back to revise (triggers new parallel brainstorm)
    )
    
    # 6. Compile without recursion_limit (set per-invoke instead)
    return workflow.compile()

# Compile the graph on import
song_writer_app = build_workflow()