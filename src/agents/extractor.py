import os
from langchain_core.prompts import ChatPromptTemplate

from src.core.state import AgentState
from src.core.llm import get_llm
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
            llm = get_llm(temperature=0)

            # Select schema based on sub_type
            schema_class = BaseSubmission
            if sub_type == "Legal500":
                schema_class = Legal500Submission

            structured_llm = llm.with_structured_output(schema_class)

            # --- Advanced Prompt Engineering for Nested Schema Extraction ---
            system_prompt = (
                "You are an elite legal data extraction agent. Your objective is to extract "
                "highly nested information for legal directories (like Legal500 or Chambers) "
                "from raw document text and map it accurately to a strict data schema.\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. ZERO HALLUCINATION: Only extract facts explicitly stated in the text. "
                "If information for a specific field is missing, you MUST leave it as null, 0, or an empty list.\n"
                "2. DEEP EXTRACTION: Pay special attention to capturing all items in nested arrays "
                "(e.g., Matters, Clients, Individual Nominations, Interview Contacts). Do not skip or summarize items if full details exist.\n"
                "3. DATA INTEGRITY: Preserve the original names, deal values, jurisdictions, and exact descriptions."
            )

            user_prompt = (
                "Target Submission Type: {sub_type}\n\n"
                "Here is the raw text extracted from the uploaded document(s):\n"
                "=========================================\n"
                "{text}\n"
                "=========================================\n\n"
                "Carefully populate the schema using ONLY the information provided above. "
                "Do not invent any missing information."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_prompt)
            ])

            chain = prompt | structured_llm
            extracted_data = chain.invoke({
                "text": extracted_text, 
                "sub_type": sub_type
            })

            # Update submission in state
            updates["submission"] = extracted_data
            updates["messages"].append("Ingestion node: Data extracted and mapped to schema successfully.")

        except Exception as e:
            updates["messages"].append(f"Ingestion node: AI extraction failed: {str(e)}")
            updates["errors"] = state.get("errors", []) + [str(e)]