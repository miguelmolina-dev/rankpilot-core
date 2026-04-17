import os
import yaml
from src.core.state import AgentState
from src.io.base64_handler import decode_base64_document
from src.io.pdf_parser import extract_text_from_pdf
from src.io.docx_manager import extract_text_from_docx
from src.core.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class ClassificationResult(BaseModel):
    input_document_type: str = Field(description="The identified type of the document (e.g. 'Legal500', 'Chambers', 'Other').")

def classification_node(state: AgentState) -> dict:
    """
    Preparation Node (Formerly Classification):
    Extracts raw text from Laravel and any uploaded base64 documents.
    Bypasses LLM classification since Laravel provides the target_submission_type.
    """
    updates = {"current_step": "preparation", "messages": []}

    decoded_file_paths = getattr(state, "decoded_file_paths", []) or []
    b64_docs = getattr(state, "base64_documents", [])

    # 1. Start the extracted_text with the raw text from Laravel!
    raw_input_text = getattr(state, "raw_input_text", "") or ""
    extracted_text = raw_input_text

    if raw_input_text.strip():
        updates["messages"].append("Preparation node: Successfully received raw text from Laravel.")

    # 2. Decode Base64 documents to the hard drive
    if b64_docs:
        for doc in b64_docs:
            filename = doc.get("filename", "")
            b64_string = doc.get("base64", "")
            if filename and b64_string:
                path = decode_base64_document(b64_string, filename)
                if path:
                    if path not in decoded_file_paths:
                        decoded_file_paths.append(path)
                    updates["messages"].append(f"Preparation node: Decoded {filename} to {path}")
                else:
                    updates["messages"].append(f"Preparation node Error: Failed to decode {filename}")

    # 3. Extract text from documents and append it to the raw text
    for file_path in decoded_file_paths:
        if not file_path:
            continue

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            text = extract_text_from_pdf(file_path)
            if text:
                extracted_text += f"\n--- Content from {os.path.basename(file_path)} ---\n{text}"
        elif ext == '.docx':
            text = extract_text_from_docx(file_path)
            if text:
                extracted_text += f"\n--- Content from {os.path.basename(file_path)} ---\n{text}"

    # 4. Update the state with paths and the beautifully merged extracted text
    updates["decoded_file_paths"] = decoded_file_paths
    updates["extracted_text"] = extracted_text

    # Trust Laravel's input for the document type
    current_target = getattr(state, "target_submission_type", None)
    if not current_target:
        current_target = "Legal500"
        updates["messages"].append("Preparation node: No target_submission_type provided. Defaulting to Legal500.")
    
    updates["target_submission_type"] = current_target

    # =========================================================
    # NEW: LOAD THE CONFIGURATION (Task: Hacer legible el código)
    # =========================================================
    yaml_mapping = {
        "Chambers_USA": "configs/chambers_usa.yaml",
        "Chambers": "configs/chambers_usa.yaml", 
        "LeadersLeague": "configs/leaders_league_advertising.yaml",
        "Legal500": "configs/legal500.yaml"
    }
    
    config_path = yaml_mapping.get(current_target, "configs/legal500.yaml")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            updates["config"] = yaml.safe_load(f) or {}
            updates["messages"].append(f"Preparation node: Loaded config from {config_path}")
    except FileNotFoundError:
        updates["config"] = {}
        updates["messages"].append(f"Preparation node Error: Could not find {config_path}")

    input_doc_type = getattr(state, "input_document_type", None)
    if not input_doc_type:
        updates["input_document_type"] = "text"

    return updates