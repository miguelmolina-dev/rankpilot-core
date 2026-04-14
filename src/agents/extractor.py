import os
from langchain_core.prompts import ChatPromptTemplate

from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import AnchorSubmission, Legal500Submission
from src.io.pdf_parser import get_submission_chunks

def merge_extracted_data(data1, data2):
    if data1 is None: return data2
    if data2 is None: return data1

    dict1 = data1.model_dump()
    dict2 = data2.model_dump()

    def deep_merge(d1, d2):
        for k, v2 in d2.items():
            if k not in d1:
                d1[k] = v2
                continue

            v1 = d1.get(k)
            if isinstance(v1, dict) and isinstance(v2, dict):
                d1[k] = deep_merge(v1, v2)
            elif isinstance(v1, list) and isinstance(v2, list):
                d1[k] = v1 + v2
            else:
                if v2 is not None and (v1 is None or v1 == "" or v1 == [] or v1 == {}):
                    d1[k] = v2
        return d1

    merged_dict = deep_merge(dict1, dict2)
    return data1.__class__(**merged_dict)

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

    extracted_text = getattr(state, "extracted_text", "") or ""
    input_document_type = getattr(state, "input_document_type", "Unknown") or "Unknown"

    target_submission_type = getattr(state, "target_submission_type", "Legal500") or "Legal500"

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

            if "chambers" in input_document_type.lower():
                chunks = get_submission_chunks(extracted_text)
                merged_data = None
                for chunk_name, chunk_text in chunks.items():
                    if not chunk_text.strip():
                        continue
                    output = chain.invoke({
                        "text": chunk_text,
                        "input_document_type": input_document_type
                    })
                    chunk_data = output.get("parsed")
                    if chunk_data:
                        merged_data = merge_extracted_data(merged_data, chunk_data)

                extracted_data = merged_data
            else:
                output = chain.invoke({
                    "text": extracted_text,
                    "input_document_type": input_document_type
                })
                extracted_data = output.get("parsed")

            if not extracted_data:
                # Provide a better error if no chunks returned anything or parsing failed
                raise ValueError("Structured LLM returned empty data or failed to parse.")

            # Update submission in state
            updates["submission"] = extracted_data
            updates["messages"].append("Ingestion node: Data mapped to Universal Schema successfully.")

        except Exception as e:
            updates["messages"].append(f"Ingestion node: AI extraction failed: {str(e)}")
            updates["errors"] = (getattr(state, "errors") or []) + [str(e)]

    else:
        updates["messages"].append("Ingestion node: No text found to extract.")

    return updates
