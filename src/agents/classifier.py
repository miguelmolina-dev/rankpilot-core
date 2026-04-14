import os
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
    Classification Node:
    Extracts text from incoming documents and identifies the input_document_type.
    """
    updates = {"current_step": "classification", "messages": []}

    decoded_file_paths = getattr(state, "decoded_file_paths", []) or []
    b64_docs = getattr(state, "base64_documents", [])

    if b64_docs:
        for doc in b64_docs:
            filename = doc.get("filename", "")
            b64_string = doc.get("base64", "")
            if filename and b64_string:
                path = decode_base64_document(b64_string, filename)
                if path:
                    if path not in decoded_file_paths:
                        decoded_file_paths.append(path)
                    updates["messages"].append(f"Decoded and saved {filename} to {path}")
                else:
                    updates["messages"].append(f"Failed to decode {filename}")

    extracted_text = ""
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

    updates["decoded_file_paths"] = decoded_file_paths

    input_document_type = getattr(state, "input_document_type", None)

    if extracted_text.strip() and not input_document_type:
        try:
            llm = get_llm(temperature=0)
            structured_llm = llm.with_structured_output(ClassificationResult)

            system_prompt = (
                "You are an expert legal document classifier. "
                "Read the beginning of the provided document text and classify what type of legal submission it is. "
                "Common types include 'Legal500', 'Chambers', or 'Other'."
            )

            # Use the first 2000 characters for classification
            text_preview = extracted_text[:2000]

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", f"Document text preview:\n\n{text_preview}\n\nClassify this document.")
            ])

            chain = prompt | structured_llm
            result = chain.invoke({})

            input_document_type = result.input_document_type
            updates["input_document_type"] = input_document_type
            updates["messages"].append(f"Classification node: Automatically classified as {input_document_type}.")
        except Exception as e:
            input_document_type = "Legal500" # Fallback
            updates["input_document_type"] = input_document_type
            updates["messages"].append(f"Classification node: LLM failed ({e}), defaulting to {input_document_type}.")
    elif input_document_type:
        updates["messages"].append(f"Classification node: Using provided input_document_type: {input_document_type}.")
    else:
        input_document_type = "Legal500" # Fallback if no text
        updates["input_document_type"] = input_document_type
        updates["messages"].append(f"Classification node: No text extracted, defaulting to {input_document_type}.")

    # Pass the extracted text via updates so ingestion_node can use it without re-extracting.
    # Note: adding to state dynamically requires it to be in AgentState, or we could just write to a temp file,
    # but we can also just let ingestion_node re-extract for simplicity, or we update AgentState to hold `extracted_text`.
    # For now, since state is typed, let's just let ingestion node extract it from decoded_file_paths as it already does,
    # or better yet, we can add `extracted_text` to AgentState if we want to avoid double work.
    # Let's just remove text extraction from ingestion_node and pass it as a file or add `extracted_text` to state.

    updates["extracted_text"] = extracted_text
    return updates
