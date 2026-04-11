from src.core.state import AgentState

def classification_node(state: AgentState) -> AgentState:
    """
    Classification Node:
    Identifies the submission_type (e.g. Legal500, Chambers).
    """
    state["current_step"] = "classification"

    # Simple logic: If not provided, we try to classify.
    if not state.get("submission_type"):
        # For demonstration, we assume we classified it as 'Legal500' based on content
        state["submission_type"] = "Legal500"

    state["messages"].append(f"Classification node: Classified as {state['submission_type']}.")
    return state
