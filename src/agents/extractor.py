import os
from langchain_core.prompts import ChatPromptTemplate

from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import AnchorSubmission, Legal500Submission

def ingestion_node(state: AgentState) -> dict:
    """
    Ingestion Node:
    Uses the extracted text and input document type to map into the Universal Feature Space (AnchorSubmission).
    """
    messages = []
    updates = {
        "current_step": "ingestion",
        "messages": messages
    }

    extracted_text = state.get("extracted_text", "")
    input_document_type = state.get("input_document_type", "Unknown")

    target_submission_type = state.get("target_submission_type", "Legal500")

    if extracted_text.strip():
        updates["messages"].append("Ingestion node: Mapping extracted text to universal feature space.")
        try:
            llm = get_llm(temperature=0)

            if target_submission_type == "Legal500":
                schema_class = Legal500Submission
            else:
                schema_class = AnchorSubmission

            structured_llm = llm.with_structured_output(schema_class, include_raw=True)

            system_prompt = (
                "You are an elite legal data extraction agent. Your objective is to extract "
                "information from raw document text into our universal feature space schema, mapping it "
                "to specific characteristics using the provided anchor tags (e.g. A1, B1, D1, etc.).\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. ZERO HALLUCINATION: Only extract facts explicitly stated in the text. "
                "If information for a specific field is missing, leave it as null, 0, or an empty list.\n"
                "2. The input document type is provided to help you understand the context of the data.\n"
                "3. Pay special attention to nested arrays (Matters, Contacts, Lawyers). Extract fully."
            )

            user_prompt = (
                "Input Document Type: {input_document_type}\n\n"
                "Here is the raw text extracted from the document(s):\n"
                "=========================================\n"
                "{text}\n"
                "=========================================\n\n"
                "Populate the universal schema. Map the data based on its content or explicitly written anchor tags."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_prompt)
            ])

            chain = prompt | structured_llm
            output = chain.invoke({
                "text": extracted_text, 
                "input_document_type": input_document_type
            })

            extracted_data = output.get("parsed")
            if not extracted_data:
                raise ValueError("Structured LLM returned empty data or failed to parse. Details: " + str(output.get("parsing_error")))

            # Update submission in state
            updates["submission"] = extracted_data
            updates["messages"].append("Ingestion node: Data mapped to Universal Schema successfully.")

        except Exception as e:
            updates["messages"].append(f"Ingestion node: AI extraction failed: {str(e)}")
            updates["errors"] = state.get("errors", []) + [str(e)]

    else:
        updates["messages"].append("Ingestion node: No text found to extract.")

    return updates
