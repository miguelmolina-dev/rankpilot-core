from src.core.state import AgentState
from src.strategies.legal500 import Legal500Strategy
from src.strategies.chambers import ChambersStrategy
from src.strategies.leaders_league import LeadersLeagueStrategy

def audit_node(state: AgentState) -> dict:
    """
    Audit Node (Gap Analysis):
    Compares the current JSON against the "Ideal Schema" of the template,
    while explicitly ignoring fields the user has dismissed.
    """
    updates = {"current_step": "audit", "messages": []}

    submission_data = getattr(state, "submission", None)
    if submission_data:
        submission_dict = submission_data.model_dump(exclude_none=True)
    else:
        submission_dict = {}

    sub_type = getattr(state, "target_submission_type", "Legal500") or "Legal500"

    if sub_type == "Legal500":
        strategy = Legal500Strategy()
    elif sub_type == "Chambers":
        strategy = ChambersStrategy()
    elif sub_type == "LeadersLeague":
        strategy = LeadersLeagueStrategy() # <--- ADD THIS
    else:
        # fallback
        strategy = Legal500Strategy()

    # 1. Get the raw gaps from the strategy
    raw_gaps = strategy.audit(submission_dict)
    
    # 2. Retrieve the fields the user wants to skip
    dismissed_gaps = getattr(state, "dismissed_gaps", [])
    
    # 3. Filter the gaps: Keep it only if the 'field' name is NOT in the dismissed list
    filtered_gaps = [gap for gap in raw_gaps if gap.get("field") not in dismissed_gaps]

    # 4. Update the state with the newly filtered list
    updates["gaps"] = filtered_gaps

    # Provide a clear log for debugging
    updates["messages"].append(
        f"Audit node: Found {len(raw_gaps)} raw gaps. "
        f"Filtered down to {len(filtered_gaps)} active gaps (ignored {len(dismissed_gaps)} dismissed)."
    )

    return updates