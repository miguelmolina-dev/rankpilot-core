from src.core.state import AgentState
from src.strategies.legal500 import Legal500Strategy
from src.strategies.chambers import ChambersStrategy

def audit_node(state: AgentState) -> dict:
    """
    Audit Node (Gap Analysis):
    Compares the current JSON against the "Ideal Schema" of the template.
    """
    updates = {"current_step": "audit", "messages": []}

    submission_data = state.get("submission")
    if submission_data:
        submission_dict = submission_data.model_dump(exclude_none=True)
    else:
        submission_dict = {}

    sub_type = state.get("target_submission_type", "Legal500")

    if sub_type == "Legal500":
        strategy = Legal500Strategy()
    elif sub_type == "Chambers":
        strategy = ChambersStrategy()
    else:
        # fallback
        strategy = Legal500Strategy()

    gaps = strategy.audit(submission_dict)
    updates["gaps"] = gaps

    updates["messages"].append(f"Audit node: Found {len(gaps)} gaps.")

    return updates
