import json
from typing import Any, Union, List, Dict, Optional, Literal
from pydantic import BaseModel, Field, ValidationError
from src.core.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState

class AnswerIntent(BaseModel):
    action: Literal["fill", "dismiss"] = Field(
        description="Must be 'fill' if the user provided valid data, or 'dismiss' if the user wants to skip."
    )
    extracted_value: str = Field(
        description="The extracted data. If it's a list or object, provide it as a valid JSON string. If it's a simple text, just the text."
    )

    class Config:
        extra = "forbid"

# ==========================================
# REFACTOR: La función debe estar afuera
# ==========================================
def update_nested_field(data, target, new_value):
    if '.' in target:
        keys = target.split('.')
        current = data
        try:
            for i, key in enumerate(keys[:-1]):
                next_key = keys[i + 1]
                
                # 1. SI LA LLAVE NO EXISTE O ES NULL, LA INICIALIZAMOS
                if isinstance(current, dict):
                    if key not in current or current[key] is None:
                        # Si el siguiente paso es un número, creamos una LISTA
                        current[key] = [] if next_key.isdigit() else {}
                    
                    # Convertimos a entero si es un índice
                    actual_key = int(key) if key.isdigit() else key
                    current = current[actual_key]
                
                elif isinstance(current, list):
                    idx = int(key)
                    # Si la lista es más corta que el índice, la extendemos
                    while len(current) <= idx:
                        current.append({} if not next_key.isdigit() else [])
                    current = current[idx]
            
            # 2. INYECCIÓN DEL VALOR FINAL
            final_key = int(keys[-1]) if keys[-1].isdigit() else keys[-1]
            
            if isinstance(current, dict):
                current[final_key] = new_value
            elif isinstance(current, list):
                idx = int(final_key)
                while len(current) <= idx:
                    current.append(None)
                current[idx] = new_value
                
            return True
        except (KeyError, IndexError, TypeError) as e:
            return False
    else:
        if target in data:
            if isinstance(data[target], list):
                if isinstance(new_value, list):
                    data[target].extend(new_value)
                else:
                    data[target].append(new_value)
            else:
                data[target] = new_value
            return True
        
        for key, value in data.items():
            if isinstance(value, dict):
                if update_nested_field(value, target, new_value):
                    return True
        return False

def process_answer_node(state: AgentState) -> dict:
    updates = {"messages": []}
    answer_data = getattr(state, "new_answer", {})
    answer_text = answer_data.get("answer", "").strip().upper()
    current_gaps = getattr(state, "gaps", []) or []
    dismissed = getattr(state, "dismissed_gaps", []) or []

    # =========================================================
    # 1. COMANDOS TÁCTICOS DE UX (El Bucle de Asistencia)
    # =========================================================
    
    # A) Saltar TODOS los casos publicables restantes
    if answer_text == "SKIP_PUBLISHABLE_MATTERS":
        updates["messages"].append("⚙️ [COMMAND] 'SKIP_PUBLISHABLE_MATTERS' detected.")
        # Filtramos solo los gaps que contengan la palabra 'matters' o 'publishable_matters'
        campos_casos = [gap.get("field") for gap in current_gaps if "publishable_matters" in gap.get("field", "")]
        updates["dismissed_gaps"] = dismissed + campos_casos
        updates["new_answer"] = {"target_field": "", "question_text": "", "answer": ""}
        return updates

    # B) Saltar TODOS los casos confidenciales restantes
    elif answer_text == "SKIP_CONFIDENTIAL_MATTERS":
        updates["messages"].append("⚙️ [COMMAND] 'SKIP_CONFIDENTIAL_MATTERS' detected.")
        # Filtramos solo los gaps confidenciales
        campos_confidenciales = [gap.get("field") for gap in current_gaps if "confidential_matters" in gap.get("field", "")]
        updates["dismissed_gaps"] = dismissed + campos_confidenciales
        updates["new_answer"] = {"target_field": "", "question_text": "", "answer": ""}
        return updates

    # C) El botón de escape de emergencia (Saltar TODO)
    elif answer_text == "SKIP_INTERVIEW":
        updates["messages"].append("⚙️ [COMMAND OVERRIDE] 'SKIP_INTERVIEW' detected. Dismissing all.")
        todos_los_campos = [gap.get("field") for gap in current_gaps]
        updates["dismissed_gaps"] = dismissed + todos_los_campos
        updates["new_answer"] = {"target_field": "", "question_text": "", "answer": ""}
        return updates
    
    if not answer_data or not answer_data.get("answer"):
        return updates

    target_field = answer_data.get("target_field")
    user_text = answer_data.get("answer")
    submission = getattr(state, "submission", None)

    updates["messages"].append(f"DEBUG: evaluating field '{target_field}' with answer: '{user_text[:30]}...'")

    schema_context = json.dumps(submission.model_json_schema()) if submission else "Unknown Schema"

    try:
        llm = get_llm(temperature=0)
        structured_llm = llm.with_structured_output(AnswerIntent)
        
        # --- MEJORA DEL PROMPT ---
        system_prompt = (
            "You are an expert data extraction AI evaluating a user's answer for a legal directory submission.\n"
            "Your goal is to extract the user's answer to populate the target field: '{field}'.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. DECIDING THE ACTION: If the user provides ANY valid, relevant information, you MUST set action to 'fill'. "
            "ONLY set action to 'dismiss' if the user explicitly says 'skip', 'ignore', 'I don't have this', or provides absolute gibberish.\n"
            "2. EXTRACTED VALUE: Output the extracted value based on the user's text. If the target is an object or list, format it strictly as a JSON string. If it's a text field, just output the clean text.\n\n"
            "Here is the strict JSON schema for context: \n{schema}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "User's answer: {answer}")
        ])
        
        chain = prompt | structured_llm
        result = chain.invoke({"field": target_field, "answer": user_text, "schema": schema_context})
        
        # --- RED DE SEGURIDAD REPARADA ---
        safe_action = result.action
        
        # Si la IA dice dismiss pero extrajo un texto largo, se equivocó y es un fill.
        if safe_action == "dismiss" and result.extracted_value and len(str(result.extracted_value)) > 15:
            safe_action = "fill"
        elif safe_action not in ["fill", "dismiss"] and result.extracted_value:
            safe_action = "fill"

        updates["messages"].append(f"DEBUG: LLM decided action='{result.action}' -> safe_action='{safe_action}'")

        # FIX: Ahora evaluamos con safe_action en lugar de result.action
        if safe_action == "dismiss":
            current_dismissed = getattr(state, "dismissed_gaps", [])
            if target_field not in current_dismissed:
                current_dismissed.append(target_field)
            updates["dismissed_gaps"] = current_dismissed
            updates["messages"].append(f"Answer Evaluator: User dismissed the '{target_field}' field.")
            
        elif safe_action == "fill":
            updates["messages"].append(f"DEBUG: Valor extraído por LLM: {str(result.extracted_value)[:100]}...")
            
            # --- NUEVO: INTERCEPTOR DE METADATA ---
            if target_field.startswith("metadata."):
                meta_key = target_field.split(".")[1] # Extrae "submission_deadline"
                metadata_obj = getattr(state, "metadata", None)
                
                if metadata_obj:
                    # Inyectamos el valor en el objeto metadata
                    setattr(metadata_obj, meta_key, result.extracted_value)
                    updates["metadata"] = metadata_obj
                    updates["messages"].append(f"SUCCESS: Metadata '{meta_key}' updated to '{result.extracted_value}'.")
                
                # Limpiamos y salimos para que no intente guardarlo en el documento
                updates["new_answer"] = {"target_field": "", "question_text": "", "answer": ""}
                return updates
            if submission:
                sub_dict = submission.model_dump()
                
                try:
                    val_to_inject = json.loads(result.extracted_value)
                    updates["messages"].append("DEBUG: El valor fue procesado como objeto/lista JSON.")
                except (json.JSONDecodeError, TypeError):
                    val_to_inject = result.extracted_value
                    updates["messages"].append("DEBUG: El valor fue procesado como string simple.")

                try:
                    success = update_nested_field(sub_dict, target_field, val_to_inject)
                    
                    if success:
                        try:
                            updates["submission"] = type(submission)(**sub_dict)
                            updates["messages"].append(f"SUCCESS: Field '{target_field}' updated.")
                        except ValidationError as e:
                            updates["submission"] = sub_dict 
                            updates["messages"].append(f"WARNING: Type mismatch in '{target_field}', stored as raw data.")
                    else:
                        updates["messages"].append(f"ERROR: Path '{target_field}' not found.")

                except Exception as e:
                    updates["messages"].append(f"CRITICAL ERROR: {str(e)}")
                    updates["new_answer"] = {"target_field": "", "question_text": "", "answer": ""}
                
            else:
                 updates["messages"].append("Answer Evaluator Error: No submission object exists.")

    except Exception as e:
        import traceback
        updates["messages"].append(f"FATAL ERROR: {str(e)} | Traceback: {traceback.format_exc()[:500]}")

    updates["new_answer"] = {"target_field": "", "question_text": "", "answer": ""}
    return updates