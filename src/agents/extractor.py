import os
import traceback
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any, Type
from pydantic import BaseModel

from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import ChambersSubmission, Legal500Submission

# ==========================================
# SCHEMA FACTORY
# ==========================================
def get_schema_class(metadata: Any) -> Type[BaseModel]:
    if not metadata:
        return ChambersSubmission # Fallback

    directory = getattr(metadata, "directory", "").lower()
    
    if "legal" in directory and "500" in directory:
        return Legal500Submission
    elif "leaders" in directory:
        return ChambersSubmission 
    else:
        return ChambersSubmission

# ==========================================
# INGESTION NODE
# ==========================================
def ingestion_node(state: AgentState) -> dict:
    messages = []
    updates = {
        "current_step": "ingestion",
        "messages": messages
    }

    extracted_text = getattr(state, "extracted_text", "") or ""
    input_document_type = getattr(state, "input_document_type", "Unknown") or "Unknown"
    metadata = getattr(state, "metadata", None)

    schema_class = get_schema_class(metadata)
    updates["messages"].append(f"Ingestion node: Selected schema {schema_class.__name__} based on metadata.")

    if extracted_text.strip():
        updates["messages"].append("Ingestion node: Mapping extracted text to universal feature space (Single Block).")
        try:
            llm = get_llm(temperature=0)
            structured_llm = llm.with_structured_output(schema_class, include_raw=True)

            system_prompt = (
                "You are an elite legal data extraction agent. Your objective is to extract "
                "information from raw document text into our universal feature space schema.\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. ZERO HALLUCINATION: Only extract facts explicitly stated in the text. "
                "If information for a specific field is missing, leave it as null, 0, or an empty list.\n"
                "2. Pay special attention to nested arrays (Matters, Contacts, Lawyers). Extract fully.\n"
                "3. STRICT TYPE ADHERENCE: If a field expects an integer (like an 'id' or 'count'), output ONLY numbers. NEVER output text strings (e.g., do not output 'Matter 1' for an ID, output exactly 1)."
            )

            user_prompt = (
                "Input Document Type: {input_document_type}\n\n"
                "Here is the raw text extracted from the document(s):\n"
                "=========================================\n"
                "{text}\n"
                "=========================================\n\n"
                "populate the schema_class."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_prompt)
            ])

            chain = prompt | structured_llm
            
            print(f"Debug: Processing {schema_class.__name__} as a single block.")
            output = chain.invoke({"text": extracted_text, "input_document_type": input_document_type})
            extracted_data = output.get("parsed")
            
            if not extracted_data:
                raise ValueError("Structured LLM returned empty data. Details: " + str(output.get("parsing_error")))

            if metadata:
                _inject_metadata_into_schema(extracted_data, metadata)

            updates["submission"] = extracted_data
            updates["messages"].append("Ingestion node: Data mapped to Universal Schema successfully.")

        except Exception as e:
            # Capturamos el error silenciosamente (puedes comentar el print_exc si no quieres ver lo rojo)
            import traceback
            traceback.print_exc() 
            updates["messages"].append(f"Ingestion node: AI extraction failed due to type error: {str(e)}")
            updates["errors"] = (getattr(state, "errors") or []) + [str(e)]
            
            # --- NUEVO: FALLBACK SEGURO (GRACEFUL DEGRADATION) ---
            # Si falló la extracción, cargamos el formulario base e inyectamos los datos de Laravel
            # para que el usuario no empiece 100% desde cero y el sistema no colapse.
            updates["messages"].append("Ingestion node: Falling back to empty schema with metadata injection.")
            empty_submission = schema_class()
            if metadata:
                _inject_metadata_into_schema(empty_submission, metadata)
            updates["submission"] = empty_submission

    else:
        updates["messages"].append("Ingestion node: No text found. Initializing empty schema for Interview Mode.")
        empty_submission = schema_class()
        if metadata:
            _inject_metadata_into_schema(empty_submission, metadata)
        updates["submission"] = empty_submission

    return updates

def _inject_metadata_into_schema(submission_obj: Any, metadata: Any):
    try:
        if hasattr(submission_obj, "A_preliminary_information") and submission_obj.A_preliminary_information is not None:
            if getattr(metadata, "practice_area", ""):
                submission_obj.A_preliminary_information.A2_practice_area = metadata.practice_area
            if getattr(metadata, "jurisdiction", ""):
                submission_obj.A_preliminary_information.A3_location_jurisdiction = metadata.jurisdiction
            if getattr(metadata, "firm_name", ""):
                submission_obj.A_preliminary_information.A1_firm_name = metadata.firm_name
                
        elif hasattr(submission_obj, "identity") and submission_obj.identity is not None:
            if getattr(metadata, "practice_area", ""):
                submission_obj.identity.practice_area = metadata.practice_area
    except Exception as e:
        print(f"--- [WARNING] Failed to inject metadata into schema: {e}")