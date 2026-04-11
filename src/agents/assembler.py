from src.core.state import AgentState
from src.strategies.legal500 import Legal500Strategy
from src.strategies.chambers import ChambersStrategy

def assembly_node(state: AgentState) -> AgentState:
    """
    Assembler Node:
    Takes the complete JSON data and uses python-docx to inject it into the final document.
    """
    state["current_step"] = "assembly"

    submission_data = state.get("submission")
    if submission_data:
        submission_dict = submission_data.model_dump(exclude_none=True)
    else:
        submission_dict = {}

    sub_type = state.get("submission_type", "Legal500")

    if sub_type == "Legal500":
        strategy = Legal500Strategy()
    elif sub_type == "Chambers":
        strategy = ChambersStrategy()
    else:
        # fallback
        strategy = Legal500Strategy()

    output_path = f"final_submission_{sub_type}.docx"
    final_doc_path = strategy.assemble(submission_dict, output_path)

    state["messages"].append(f"Assembly node: Document assembled at {final_doc_path}.")

    return state
