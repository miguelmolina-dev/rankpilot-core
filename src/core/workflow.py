from langgraph.graph import StateGraph, END
from typing import Literal

from src.core.state import AgentState
from src.agents.extractor import ingestion_node
from src.agents.classifier import classification_node
from src.agents.auditor import audit_node
from src.agents.interrogator import interrogator_node
from src.agents.assembler import assembly_node
from src.agents.updater import update_node
from src.agents.sanitizer import sanitizer_node

def route_after_audit(state: AgentState) -> Literal["interrogator_node", "assembly_node"]:
    """
    If there are gaps, route to the interrogator to ask the user.
    If no gaps, route to assembly to build the final document.
    """
    gaps = getattr(state, "gaps", []) or []
    if len(gaps) > 0:
        return "interrogator_node"
    return "assembly_node"

def route_entry(state: AgentState) -> Literal["update_node", "classification_node"]:
    """
    If Laravel sends a state containing a user's answer, start at the update_node.
    Otherwise (first run), start at the classification_node.
    """
    new_answer = getattr(state, "new_answer", {}) or {}
    if new_answer.get("answer"):
        return "update_node"
    return "classification_node"

def build_workflow() -> StateGraph:
    """
    Builds the LangGraph state machine for the FastAPI server.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("ingestion_node", ingestion_node)
    workflow.add_node("classification_node", classification_node)
    workflow.add_node("audit_node", audit_node)
    workflow.add_node("interrogator_node", interrogator_node)
    workflow.add_node("assembly_node", assembly_node)
    workflow.add_node("update_node", update_node)
    workflow.add_node("sanitizer_node", sanitizer_node)

    # Set Entry Point conditionally based on the JSON payload from Laravel
    workflow.set_conditional_entry_point(
        route_entry,
        {
            "update_node": "update_node",
            "classification_node": "classification_node"
        }
    )

    # Define linear flow for data processing
    workflow.add_edge("classification_node", "ingestion_node")
    workflow.add_edge("ingestion_node", "sanitizer_node")
    
    # User updates ALSO go through the Sanitizer/Copywriter
    workflow.add_edge("update_node", "sanitizer_node")
    
    workflow.add_edge("sanitizer_node", "audit_node")

    # Define conditional routing based on gaps
    workflow.add_conditional_edges(
        "audit_node",
        route_after_audit,
        {
            "interrogator_node": "interrogator_node",
            "assembly_node": "assembly_node"
        }
    )

    # BOTH of these nodes route to END. 
    # This naturally "pauses" the workflow and returns the JSON state to FastAPI!
    workflow.add_edge("interrogator_node", END)
    workflow.add_edge("assembly_node", END)

    # ARCHITECTURE UPGRADE: 
    # We compile with NO checkpointer and NO interrupts. 
    # Laravel handles the memory. LangGraph just executes the graph.
    return workflow.compile()