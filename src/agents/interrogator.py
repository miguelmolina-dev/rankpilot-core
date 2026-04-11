from src.core.state import AgentState

def interrogator_node(state: AgentState) -> AgentState:
    """
    Interrogator Node:
    Generates dynamic questions for the fields marked as null or missing (gaps).
    """
    state["current_step"] = "interrogator"

    gaps = state.get("gaps", [])
    questions = []

    for gap in gaps:
        # In a real implementation, this might call an LLM using src.agents.prompts
        field = gap.get("field", "unknown")
        questions.append(f"We are missing information for '{field}'. Could you provide details?")

    state["questions"] = questions
    state["messages"].append(f"Interrogator node: Generated {len(questions)} questions.")

    return state
