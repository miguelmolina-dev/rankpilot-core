import json
from typing import Any, Union, List, Dict, Optional
from pydantic import BaseModel, Field, ValidationError
from src.core.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState

class AnswerIntent(BaseModel):
    action: str = Field(
        description="Must be 'fill' if the user provided valid data, or 'dismiss' if the user wants to skip."
    )
    # Cambiamos a str para evitar el error 400 de esquemas complejos del LLM
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
            for key in keys[:-1]:
                # --- ESTE ES EL FIX ---
                # Si el nodo padre es None o no existe, lo creamos como un dict vacío
                if key not in current or current[key] is None:
                    current[key] = {}
                
                if key.isdigit():
                    key = int(key)
                current = current[key]
            
            final_key = keys[-1]
            if final_key.isdigit():
                final_key = int(final_key)
            
            # Lógica de inyección (igual a la anterior)
            if isinstance(current, dict) and final_key in current and isinstance(current[final_key], list):
                if isinstance(new_value, list):
                    current[final_key].extend(new_value)
                else:
                    current[final_key].append(new_value)
            else:
                current[final_key] = new_value
            return True
        except (KeyError, IndexError, TypeError) as e:
            # Puedes imprimir el error e aquí para más debug si fuera necesario
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are evaluating a user's answer for a legal directory submission. Target field: '{field}'.\n\n"
                       "CRITICAL: You MUST output the 'extracted_value' as a valid string. If the target is an object or list, format it as a JSON string.\n"
                       "Here is the strict JSON schema: \n{schema}"),
            ("user", "User's answer: {answer}")
        ])
        
        chain = prompt | structured_llm
        result = chain.invoke({"field": target_field, "answer": user_text, "schema": schema_context})
        updates["messages"].append(f"DEBUG: LLM decided action='{result.action}'")

        if result.action == "dismiss":
            current_dismissed = getattr(state, "dismissed_gaps", [])
            if target_field not in current_dismissed:
                current_dismissed.append(target_field)
            updates["dismissed_gaps"] = current_dismissed
            updates["messages"].append(f"Answer Evaluator: User dismissed the '{target_field}' field.")
            
        elif result.action == "fill":
            updates["messages"].append(f"DEBUG: Valor extraído por LLM: {result.extracted_value}")
            if submission:
                sub_dict = submission.model_dump()
                
                # --- INTENTO DE DECODIFICACIÓN ---
                try:
                    val_to_inject = json.loads(result.extracted_value)
                    updates["messages"].append("DEBUG: El valor fue procesado como objeto/lista JSON.")
                except (json.JSONDecodeError, TypeError):
                    val_to_inject = result.extracted_value
                    updates["messages"].append("DEBUG: El valor fue procesado como string simple.")

                # LLAMADA A LA FUNCIÓN (Ahora sí existe)
                success = update_nested_field(sub_dict, target_field, val_to_inject)
                
                if success:
                    try:
                        updates["submission"] = type(submission)(**sub_dict)
                        updates["messages"].append(f"Answer Evaluator: Successfully filled '{target_field}'.")
                    except ValidationError as e:
                        updates["messages"].append(f"Answer Evaluator Error: Pydantic rejected the AI's format. Error: {e}")
                else:
                    updates["messages"].append(f"Answer Evaluator Error: Could not locate '{target_field}' in the schema.")
            else:
                 updates["messages"].append("Answer Evaluator Error: No submission object exists.")

    except Exception as e:
        import traceback
        updates["messages"].append(f"FATAL ERROR: {str(e)} | Traceback: {traceback.format_exc()[:500]}")

    updates["new_answer"] = {"target_field": "", "question_text": "", "answer": ""}
    return updates