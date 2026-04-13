from langgraph.graph import StateGraph, END
from typing import Literal

from src.core.state import AgentState
from src.agents.extractor import ingestion_node
from src.agents.classifier import classification_node
from src.agents.auditor import audit_node
from src.agents.interrogator import interrogator_node
from src.agents.assembler import assembly_node
from src.agents.updater import update_node

def route_after_audit(state: AgentState) -> Literal["interrogator_node", "assembly_node"]:
    """
    If there are gaps, go to interrogator.
    If no gaps, go to assembly.
    """
    gaps = state.get("gaps", [])
    if len(gaps) > 0:
        return "interrogator_node"
    return "assembly_node"

def route_entry(state: AgentState) -> Literal["update_node", "classification_node"]:
    """
    If new_answer has an answer, we route to update_node.
    Otherwise, we route to ingestion_node (initial start).
    """
    new_answer = state.get("new_answer", {})
    if new_answer.get("answer"):
        return "update_node"
    return "classification_node"

def build_workflow(checkpointer=None, interrupt_before=None) -> StateGraph:
    """
    Builds the LangGraph state machine.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("ingestion_node", ingestion_node)
    workflow.add_node("classification_node", classification_node)
    workflow.add_node("audit_node", audit_node)
    workflow.add_node("interrogator_node", interrogator_node)
    workflow.add_node("assembly_node", assembly_node)
    workflow.add_node("update_node", update_node)

    # Set Entry Point conditionally based on state
    workflow.set_conditional_entry_point(
        route_entry,
        {
            "update_node": "update_node",
            "classification_node": "classification_node"
        }
    )

    # Define simple linear flow for early steps
    workflow.add_edge("classification_node", "ingestion_node")
    workflow.add_edge("ingestion_node", "audit_node")
    workflow.add_edge("update_node", "audit_node")

    # Define conditional routing
    workflow.add_conditional_edges(
        "audit_node",
        route_after_audit,
        {
            "interrogator_node": "interrogator_node",
            "assembly_node": "assembly_node"
        }
    )

    # Interrogator routes to END (pauses workflow for Laravel)
    workflow.add_edge("interrogator_node", END)

    # End after assembly
    workflow.add_edge("assembly_node", END)

    return workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt_before)
