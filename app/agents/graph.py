import logging
from langgraph.graph import StateGraph, END
from app.models.state import ChaosPilotState
from app.agents.explorer import discovery_node
from app.agents.planner import planner_node
from app.agents.runner import runner_node
from app.agents.reflector import reflect_node
from app.agents.triage import triage_node
from app.agents.reporter import reporter_node

logger = logging.getLogger(__name__)

def create_chaospilot_graph():
    """
    Constructs the stateful LangGraph workflow for ChaosPilot autonomous QA execution,
    including self-healing reflection loops.
    """
    builder = StateGraph(ChaosPilotState)

    # Add Nodes
    builder.add_node("discovery", discovery_node)
    builder.add_node("planner", planner_node)
    builder.add_node("runner", runner_node)
    builder.add_node("reflector", reflect_node)
    builder.add_node("triage", triage_node)
    builder.add_node("reporter", reporter_node)

    # Define State Flow Edges
    builder.set_entry_point("discovery")
    
    # Conditional branching if discovery fails
    def check_discovery(state: ChaosPilotState) -> str:
        if state.status == "FAILED":
            return "reporter"
        return "planner"

    builder.add_conditional_edges("discovery", check_discovery, {"planner": "planner", "reporter": "reporter"})
    builder.add_edge("planner", "runner")
    builder.add_edge("runner", "reflector")
    builder.add_edge("reflector", "triage")
    builder.add_edge("triage", "reporter")
    builder.add_edge("reporter", END)

    return builder.compile()

chaospilot_app = create_chaospilot_graph()
