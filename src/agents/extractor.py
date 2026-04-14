import os
import traceback
from langchain_core.prompts import ChatPromptTemplate

from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import AnchorSubmission, Legal500Submission
from src.io.pdf_data_chunking import chunk_chambers_submission

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
            print(f"Debug: Target submission type is {target_submission_type}")
            print(f"Debug: Input document type is {input_document_type}")
            print(f"Debug: Extracted text length is {len(extracted_text)} characters")

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
                "populate the schema_class.\n"
                "Map the data based on its content or explicitly written anchor tags."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_prompt)
            ])

            chain = prompt | structured_llm
            # --- NEW EXTRACTION LOGIC ---
            if input_document_type == "Chambers":
                print("Debug: Chambers document detected. Applying chunking strategy.")
                chunks = chunk_chambers_submission(extracted_text)
                final_merged_dict = {}

                for chunk_name, chunk_text in chunks.items():
                    print(f"Debug: Processing chunk {chunk_name} ({len(chunk_text)} chars)")
                    output = chain.invoke({
                        "text": chunk_text, 
                        "input_document_type": input_document_type
                    })
                    
                    parsed_chunk = output.get("parsed")
                    
                    if parsed_chunk:
                        # Exclude unset/none values so empty fields in one chunk 
                        # don't overwrite valid data from a previous chunk
                        chunk_dict = parsed_chunk.dict(exclude_unset=True, exclude_none=True)
                        
                        # Smart merge logic
                        for key, value in chunk_dict.items():
                            if isinstance(value, list):
                                # Append lists (e.g., Lawyers, Matters)
                                if key not in final_merged_dict:
                                    final_merged_dict[key] = []
                                final_merged_dict[key].extend(value)
                            elif isinstance(value, dict) and key in final_merged_dict and isinstance(final_merged_dict[key], dict):
                                # Merge nested dictionaries
                                final_merged_dict[key].update(value)
                            else:
                                # Overwrite strings/integers (e.g., Firm Name)
                                final_merged_dict[key] = value
                    else:
                        print(f"Warning: Chunk {chunk_name} failed to parse. Details: {output.get('parsing_error')}")

                # Rebuild the final Pydantic object from the merged dictionary
                if not final_merged_dict:
                     raise ValueError("Structured LLM returned empty data across all chunks.")
                extracted_data = schema_class(**final_merged_dict)

            else:
                # Fallback for non-Chambers documents (processes as a single block)
                print("Debug: Standard document detected. Processing as a single block.")
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
            traceback.print_exc()
            updates["messages"].append(f"Ingestion node: AI extraction failed: {str(e)}")
            updates["errors"] = (getattr(state, "errors") or []) + [str(e)]

    else:
        updates["messages"].append("Ingestion node: No text found to extract.")

    return updates
