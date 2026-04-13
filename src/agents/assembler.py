from src.core.state import AgentState
from src.strategies.legal500 import Legal500Strategy
from src.strategies.chambers import ChambersStrategy
from src.io.base64_encoder import encode_file_to_base64

def assembly_node(state: AgentState) -> dict:
    """
    Assembler Node:
    Takes the complete JSON data and uses python-docx to inject it into the final document.
    """
    updates = {"current_step": "assembly", "messages": []}

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

    output_path = "data/processed"
    final_doc_path = strategy.assemble(submission_dict, output_path)

    updates["messages"].append(f"Assembly node: Document assembled at {final_doc_path}.")

    encoded_file = encode_file_to_base64(final_doc_path)
    if encoded_file:
        updates["output_base64"] = encoded_file

    return updates
