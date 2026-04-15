from pydantic import BaseModel, Field
from core.state import AgentState
from src.core.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate

# 1. Define the Structured Output for the AI
class AnswerIntent(BaseModel):
    action: str = Field(description="Must be 'fill' if the user provided valid data, or 'dismiss' if the user wants to skip, doesn't know, or says it does not exist.")
    extracted_value: str = Field(description="If action is 'fill', format the user's data for the document. If 'dismiss', leave blank.")

def process_answer_node(state: AgentState) -> dict:
    updates = {"messages": []}
    answer_data = getattr(state, "new_answer", {})
    
    if not answer_data or not answer_data.get("answer"):
        return updates

    target_field = answer_data.get("target_field")
    user_text = answer_data.get("answer")

    # 2. Ask the LLM to evaluate the user's intent
    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(AnswerIntent)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are evaluating a user's answer for a legal submission form. The target field is '{field}'. Decide if the user provided valid information to fill the field, or if they are expressing a desire to skip, ignore, or state that the item does not exist."),
        ("user", "User's answer: {answer}")
    ])
    
    chain = prompt | structured_llm
    result = chain.invoke({"field": target_field, "answer": user_text})

    # 3. Route the logic based on the AI's classification
    if result.action == "dismiss":
        # Add the field to the dismissed list!
        current_dismissed = getattr(state, "dismissed_gaps", [])
        if target_field not in current_dismissed:
            current_dismissed.append(target_field)
            
        updates["dismissed_gaps"] = current_dismissed
        updates["messages"].append(f"Answer Evaluator: User dismissed the '{target_field}' field. Ignoring for future loops.")
        
    elif result.action == "fill":
        # Update your submission object here
        submission = getattr(state, "submission")
        # ... logic to inject result.extracted_value into submission ...
        updates["submission"] = submission
        updates["messages"].append(f"Answer Evaluator: Successfully filled '{target_field}'.")

    # Clear the answer so we don't process it again
    updates["new_answer"] = {}
    return updates