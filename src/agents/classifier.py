from src.core.state import AgentState

def classification_node(state: AgentState) -> dict:
    """
    Classification Node:
    Identifies the submission_type (e.g. Legal500, Chambers).
    """
    updates = {"current_step": "classification", "messages": []}

    submission_type = state.get("submission_type")
    # Simple logic: If not provided, we try to classify.
    if not submission_type:
        # For demonstration, we assume we classified it as 'Legal500' based on content
        submission_type = "Legal500"
        updates["submission_type"] = submission_type

    updates["messages"].append(f"Classification node: Classified as {submission_type}.")
    return updates
