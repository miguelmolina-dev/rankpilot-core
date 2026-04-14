import os
import time
import shutil
import re
from src.core.state import AgentState
from src.strategies.legal500 import Legal500Strategy
from src.strategies.chambers import ChambersStrategy
from src.io.base64_encoder import encode_file_to_base64

def sanitize_filename(name: str) -> str:
    """Removes invalid characters to make the firm name safe for the file system."""
    name = str(name).strip()
    # Keep only alphanumeric characters, spaces, hyphens, and underscores
    name = re.sub(r'(?u)[^-\w\s]', '', name)
    # Replace spaces and hyphens with a single underscore
    return re.sub(r'[-\s]+', '_', name)

def assembly_node(state: AgentState) -> dict:
    """
    Assembler Node:
    Takes the complete JSON data, injects it into the template, 
    names it cleanly, and removes any temporary child folders.
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

    # 1. Extract and sanitize the Firm Name for the file
    raw_firm_name = "Unknown_Firm"
    if "identity" in submission_dict and "firm_name" in submission_dict["identity"]:
        raw_firm_name = submission_dict["identity"]["firm_name"] or "Unknown_Firm"
    
    firm_name = sanitize_filename(raw_firm_name)
    timestamp = int(time.time())
    
    # Define our perfect final file name
    final_filename = f"{firm_name}_{sub_type}_{timestamp}.docx"

    # 2. Setup the paths
    base_dir = os.path.join("data", "processed")
    temp_dir = os.path.join(base_dir, f"temp_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)
    
    final_doc_path = os.path.join(base_dir, final_filename)

    try:
        # 3. Let the strategy assemble the document inside the temporary directory
        generated_path = strategy.assemble(submission_dict, temp_dir)
        
        # 4. Move it to the base directory and apply our custom name
        shutil.move(generated_path, final_doc_path)
        updates["messages"].append(f"Assembly node: Document successfully assembled at {final_doc_path}.")

        # 5. Encode the cleanly named file
        encoded_file = encode_file_to_base64(final_doc_path)
        if encoded_file:
            updates["output_base64"] = encoded_file
        else:
            updates["messages"].append("Assembly node Error: encode_file_to_base64 returned None.")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        updates["messages"].append(f"Assembly node Error: Failed to assemble document: {str(e)}")
        
    finally:
        # 6. CLEANUP: Delete the temporary folder and whatever was left inside it
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    return updates