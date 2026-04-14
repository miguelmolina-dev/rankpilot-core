import os
import time
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
    else:
        # fallback
        strategy = Legal500Strategy()

    # FIX: Ensure the directory exists and provide a full file path
    output_dir = os.path.join("data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate a unique filename using a timestamp to avoid overwriting files
    filename = f"{sub_type}_submission_{int(time.time())}.docx"
    output_path = os.path.join(output_dir, filename)

    try:
        # This will now correctly save to data/processed/Legal500_submission_171...docx
        final_doc_path = strategy.assemble(submission_dict, output_path)
        updates["messages"].append(f"Assembly node: Document assembled at {final_doc_path}.")

        # Encode the newly created file
        encoded_file = encode_file_to_base64(final_doc_path)
        if encoded_file:
            updates["output_base64"] = encoded_file
        else:
            updates["messages"].append("Assembly node Error: encode_file_to_base64 returned None.")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        updates["messages"].append(f"Assembly node Error: Failed to assemble document: {str(e)}")

    return updates