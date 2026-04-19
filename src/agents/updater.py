import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import ChambersSubmission, Legal500Submission

# --- NUEVOS ESQUEMAS DE PARCHE ---
class FieldUpdate(BaseModel):
    field_name: str = Field(description="The exact name of the field from the schema (e.g., 'firm_name', 'work_highlights_summaries').")
    json_value: str = Field(description="The new extracted data formatted strictly as a JSON string. If it's a string, wrap in quotes. If an array/list, format as a JSON array.")

class SubmissionPatch(BaseModel):
    updates: List[FieldUpdate] = Field(description="List of fields to update based on the user's answer.")

# --- FUNCIÓN RECURSIVA PARA ACTUALIZAR EL DICCIONARIO ---
def deep_update_field(data: dict, target_field: str, new_value: Any) -> bool:
    """Recursively searches for a key in a nested dict and updates or merges its value."""
    if target_field in data:
        # Prevent "Whack-a-Mole" bug: 
        # If the existing data is a dictionary AND the new data is a dictionary, MERGE them!
        if isinstance(data[target_field], dict) and isinstance(new_value, dict):
            data[target_field].update(new_value)
        else:
            # For strings, booleans, lists, or if the current value is None, just overwrite
            data[target_field] = new_value
        return True
        
    for key, value in data.items():
        if isinstance(value, dict):
            if deep_update_field(value, target_field, new_value):
                return True
    return False

def update_node(state: AgentState) -> dict:
    """
    Update Node:
    Receives an incoming state with a user answer in new_answer["answer"].
    Merges the answer into the existing submission schema.
    """
    updates = {"current_step": "update", "messages": []}

    new_answer_dict = getattr(state, "new_answer", {}) or {}
    question_text = new_answer_dict.get("question_text", "")
    answer_text = new_answer_dict.get("answer", "")
    target_field = new_answer_dict.get("target_field", "unknown")

    history = getattr(state, "history", []) or []

    if answer_text:
        qa_pair = f"Q_Text: {question_text} | Answer: {answer_text}"
        history.append(qa_pair)
        updates["history"] = history
        updates["messages"].append(f"Update node: Received answer for '{question_text}'")

        submission_data = getattr(state, "submission", None)
        target_submission_type = getattr(state, "target_submission_type", "Legal500") or "Legal500"

        if submission_data:
            current_submission_dict = submission_data.model_dump()
        else:
            current_submission_dict = {}

        # Get list of missing fields to give context to the LLM (Saves prompt tokens!)
        gaps = getattr(state, "gaps", []) or []
        
        # Formateamos una lista legible para el LLM: "- campo: descripción"
        missing_fields_context = "\n".join(
            [f"- {gap.get('field', 'Unknown')}: {gap.get('reason', 'No description provided')}" for gap in gaps]
        )

        try:
            llm = get_llm(temperature=0.0)

            if target_submission_type == "Legal500":
                schema_class = Legal500Submission
            elif target_submission_type == "Chambers":
                schema_class = ChambersSubmission

            # USAMOS EL PATCH EN LUGAR DEL SCHEMA COMPLETO
            structured_llm = llm.with_structured_output(SubmissionPatch, include_raw=True)
            schema_blueprint = json.dumps(schema_class.model_json_schema())

            system_prompt = (
                "### 1. PERSONA ###\n"
                "You are an elite global Data Architect and Legal Analyst. You translate and extract data from user answers "
                "into structured JSON objects in STRICT PROFESSIONAL ENGLISH.\n\n"
                
                "### 2. CONTEXT ###\n"
                "You are receiving a raw answer from a user (which might be in Spanish or another language). "
                "You must map this data to the English-based Architectural Blueprint below:\n"
                "REFERENCE SCHEMA BLUEPRINT:\n"
                "{schema_blueprint}\n\n"
                
                "### 3. THE TASK ###\n"
                "Analyze the answer, TRANSLATE any non-English information into professional English, and update the 'Target Field'. "
                "Perform OPPORTUNISTIC EXTRACTION for other missing fields found in the text.\n\n"
                
                "### 4. CRITICAL CONSTRAINTS (MUST FOLLOW) ###\n"
                "- LANGUAGE: All 'json_value' outputs MUST be in English, even if the user answered in another language.\n"
                "- PRECISION TARGETING: Match the exact leaf-node names from the schema.\n"
                "- STRICT TYPING: Match the data structure (List, Dict, Str) dictated by the Blueprint.\n"
                "- NO HALLUCINATIONS: Do not invent facts, only translate and structure what was provided.\n\n"
                
                "### 5. FORMAT ###\n"
                "Output a list of FieldUpdate objects. The `json_value` field MUST be a perfectly escaped JSON string."
            )

            # Removed the 'f' prefix. These are now LangChain variables.
            user_prompt = (
                "Target Field to Update: {target_field}\n\n"
                "Other Missing Fields & Descriptions:\n{missing_fields_context}\n\n"
                "Question Asked to User:\n{question_text}\n\n"
                "User's Answer:\n{answer_text}\n\n"
                "Provide the updates list."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])

            chain = prompt | structured_llm
            
            # NEW: Pass the actual variables here! LangChain will safely inject them.
            output = chain.invoke({
                "schema_blueprint": schema_blueprint,
                "target_field": target_field,
                "missing_fields_context": missing_fields_context,
                "question_text": question_text,
                "answer_text": answer_text
            })

            patch_data = output.get("parsed")
            if not patch_data:
                raise ValueError("Structured LLM returned empty data or failed to parse.")

            # INYECTAR LOS CAMBIOS EN EL DICCIONARIO
            for update in patch_data.updates:
                try:
                    # Convertir el string de JSON a un objeto de Python
                    val = json.loads(update.json_value)
                except json.JSONDecodeError:
                    # Fallback por si el LLM olvida las comillas
                    val = update.json_value
                
                deep_update_field(current_submission_dict, update.field_name, val)
                updates["messages"].append(f"Update node: Successfully patched field '{update.field_name}'.")

            # RE-VALIDAR CON EL ESQUEMA ORIGINAL
            if target_submission_type == "Legal500":
                updated_submission = Legal500Submission(**current_submission_dict)
            elif target_submission_type == "Chambers":
                updated_submission = ChambersSubmission(**current_submission_dict)

            updates["submission"] = updated_submission

        except Exception as e:
            import traceback
            traceback.print_exc()
            updates["messages"].append(f"LLM update failed: {e}. The submission was not updated with the new answer.")

    updates["new_answer"] = {"question_text": "", "answer": ""}

    return updates
