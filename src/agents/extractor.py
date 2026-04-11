import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.core.state import AgentState
from src.core.schemas import Legal500Submission, BaseSubmission
from src.io.base64_handler import decode_base64_document
from src.io.pdf_parser import extract_text_from_pdf
from src.io.docx_manager import extract_text_from_docx

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

    # Extract text from decoded files if available
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

    updates = {
        "current_step": "ingestion",
        "decoded_file_paths": decoded_file_paths,
        "messages": messages
    }

    sub_type = state.get("submission_type", "Legal500")

    # If there is extracted text, map it to the state using an AI Agent
    if extracted_text.strip():
        updates["messages"].append("Ingestion node: Extracting and mapping data from files using AI agent.")
        try:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)

            # Select schema based on sub_type
            schema_class = BaseSubmission
            if sub_type == "Legal500":
                schema_class = Legal500Submission

            structured_llm = llm.with_structured_output(schema_class)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert AI assistant that extracts information from raw text and maps it accurately into the provided schema for legal submissions. You extract data precisely without hallucinating."),
                ("user", "Extract the relevant information from the following text and populate the structured schema.\n\nText:\n{text}")
            ])

            chain = prompt | structured_llm
            extracted_data = chain.invoke({"text": extracted_text})

            # Update submission in state
            updates["submission"] = extracted_data
            updates["messages"].append("Ingestion node: Data mapped successfully.")

        except Exception as e:
            updates["messages"].append(f"Ingestion node: AI extraction failed: {str(e)}")
    else:
        updates["messages"].append("Ingestion node: No text extracted to map.")

    return updates
