# app/graph/workflow.py
#
# The main LangGraph workflow.

from langgraph.graph import StateGraph, END
from app.graph.state import SongWritingState

# --- Import ALL async agent nodes ---
from app.agents.producer import producer_node
from app.agents.lyracist import lyracist_node
from app.agents.researcher import researcher_node
from app.agents.brainstormers import brainstormer_node
from app.agents.critics import critics_node 

def create_workflow():
    """
    Creates the LangGraph workflow.
    """
    
    workflow = StateGraph(SongWritingState)

    # --- Add all agent nodes ---
    workflow.add_node("producer", producer_node)
    workflow.add_node("lyracist", lyracist_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("brainstormers", brainstormer_node)
    workflow.add_node("critics", critics_node)

    # The entry point is always the Producer
    workflow.set_entry_point("producer")

    # --- Define the routing logic ---
    def route_from_producer(state: SongWritingState):
        """
        Reads the 'next_step' field set by the producer
        and routes to the corresponding node.
        """
        next_step = state.get("next_step", "producer").lower()
        
        if next_step == "lyracist":
            return "lyracist"
        if next_step == "researcher":
            return "researcher"
        if next_step == "brainstormers":
            return "brainstormers"
        if next_step == "terminate":
            return END
        
        return "producer"

    # --- Add the graph edges ---

    # 1. The Producer routes to all creative/research nodes
    workflow.add_conditional_edges(
        "producer",
        route_from_producer,
        {
            "lyracist": "lyracist",
            "researcher": "researcher",
            "brainstormers": "brainstormers",
            END: END
        }
    )

    # 2. The Lyracist ALWAYS goes to the Critic for scoring
    workflow.add_edge("lyracist", "critics")

    # 3. The Critic ALWAYS goes back to the Producer for re-evaluation
    workflow.add_edge("critics", "producer")
    
    # 4. Other nodes loop back to the Producer directly
    workflow.add_edge("researcher", "producer")
    workflow.add_edge("brainstormers", "producer")

    # Compile the graph
    app = workflow.compile()
    return app