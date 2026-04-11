from src.core.state import AgentState

from src.io.base64_handler import decode_base64_document

def ingestion_node(state: AgentState) -> dict:
    """
    Ingestion Node:
    Loads previous documents (from base64) and fills what it can into the Mega Vector JSON (AgentState.submission).
    """
    messages = []
    decoded_file_paths = state.get("decoded_file_paths", []) or []

    # Process base64 documents if present
    b64_docs = state.get("base64_documents", [])
    if b64_docs:
        for doc in b64_docs:
            filename = doc.get("filename", "")
            b64_string = doc.get("base64", "")
            if filename and b64_string:
                path = decode_base64_document(b64_string, filename)
                if path:
                    decoded_file_paths.append(path)
                    messages.append(f"Decoded and saved {filename} to {path}")
                else:
                    messages.append(f"Failed to decode {filename}")

    # This node would typically interact with vector databases and LLM extraction using the decoded files
    messages.append("Ingestion node: Parsed documents into initial submission.")

    return {
        "current_step": "ingestion",
        "decoded_file_paths": decoded_file_paths,
        "messages": messages,
        "gaps": state.get("gaps", []),
        "questions": state.get("questions", [])
    }
