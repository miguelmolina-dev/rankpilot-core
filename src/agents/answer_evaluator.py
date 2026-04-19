import json
from typing import Any, Union, List, Dict
from pydantic import BaseModel, Field, ValidationError
from src.core.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState

class AnswerIntent(BaseModel):
    action: str = Field(
        description="Must be 'fill' if the user provided valid data, or 'dismiss' if the user wants to skip."
    )
    extracted_value: Union[List[Dict[str, Any]], Dict[str, Any], str] = Field(
        description="The formatted data. Must exactly match the target field's expected format."
    )

    # ==========================================
    # EL FIX PARA EL LLM (OpenAI/Gemini Strict)
    # ==========================================
    class Config:
        extra = "forbid"

def process_answer_node(state: AgentState) -> dict:
    updates = {"messages": []}
    answer_data = getattr(state, "new_answer", {})
    
    if not answer_data or not answer_data.get("answer"):
        return updates

    target_field = answer_data.get("target_field")
    user_text = answer_data.get("answer")
    submission = getattr(state, "submission", None)

    schema_context = json.dumps(submission.model_json_schema()) if submission else "Unknown Schema"

    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(AnswerIntent)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are evaluating a user's answer for a legal directory submission. Target field: '{field}'.\n\n"
                   "CRITICAL INSTRUCTIONS:\n"
                   "1. Action: Decide if the user provided valid info ('fill') or explicitly wants to skip/has no data ('dismiss').\n"
                   "2. Extracted Value: You MUST format the extracted data to perfectly match the JSON schema requirements for '{field}'.\n"
                   "3. If '{field}' requires an array of objects, return a LIST OF DICTIONARIES using the exact property keys defined in the schema.\n\n"
                   "Here is the strict JSON schema for the entire submission: \n{schema}"),
        ("user", "User's answer: {answer}")
    ])
    
    chain = prompt | structured_llm
    result = chain.invoke({"field": target_field, "answer": user_text, "schema": schema_context})

    if result.action == "dismiss":
        current_dismissed = getattr(state, "dismissed_gaps", [])
        if target_field not in current_dismissed:
            current_dismissed.append(target_field)
            
        updates["dismissed_gaps"] = current_dismissed
        updates["messages"].append(f"Answer Evaluator: User dismissed the '{target_field}' field.")
        
    elif result.action == "fill":
        if submission:
            sub_dict = submission.model_dump()
            
            # ==========================================
            # NEW: The Universal Injector Function
            # ==========================================
            def update_nested_field(data, target, new_value):
                # CASE 1: Chambers Style (Dot-notation path, e.g., 'matters.1.client')
                if '.' in target:
                    keys = target.split('.')
                    current = data
                    try:
                        # Traverse down to the second-to-last item
                        for key in keys[:-1]:
                            if key.isdigit():
                                key = int(key) # Handle array index
                            current = current[key]
                        
                        # Grab the final key (the actual destination)
                        final_key = keys[-1]
                        if final_key.isdigit():
                            final_key = int(final_key)
                        
                        # Inject the value
                        if isinstance(current, dict) and final_key in current and isinstance(current[final_key], list):
                            if isinstance(new_value, list):
                                current[final_key].extend(new_value)
                            else:
                                current[final_key].append(new_value)
                        else:
                            current[final_key] = new_value
                        return True
                    except (KeyError, IndexError, TypeError):
                        return False

                # CASE 2: Legal500 Style (Recursive scanner, e.g., 'matters')
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
            # ==========================================

            success = update_nested_field(sub_dict, target_field, result.extracted_value)
            
            if success:
                try:
                    updates["submission"] = type(submission)(**sub_dict)
                    updates["messages"].append(f"Answer Evaluator: Successfully filled '{target_field}'.")
                except ValidationError as e:
                    updates["messages"].append(f"Answer Evaluator Error: Pydantic rejected the AI's format for '{target_field}'. Error: {e}")
            else:
                updates["messages"].append(f"Answer Evaluator Error: Could not locate '{target_field}' in the schema.")
        else:
             updates["messages"].append("Answer Evaluator Error: No submission object exists.")

    updates["new_answer"] = {}
    return updates