from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm

class StrategicQuestion(BaseModel):
    question: str = Field(
        description="A strategic question asking for the specific missing information."
    )

def interrogator_node(state: AgentState) -> dict:
    """
    Interrogator Node:
    Generates dynamic, strategic questions for the fields marked as null or missing (gaps)
    using an LLM.
    """
    updates = {"current_step": "interrogator", "messages": []}

    gaps = getattr(state, "gaps", []) or []
    question = ""

    if gaps:
        try:
            llm = get_llm(temperature=0.2)
            structured_llm = llm.with_structured_output(StrategicQuestion)

            system_prompt = (
                "You are an expert legal ranking strategist advising a law firm. "
                "The firm is preparing a submission for legal directories (like Chambers or Legal500), "
                "but a specific required field is missing. "
                "Generate a single clear, professional, and strategic question to ask the attorneys "
                "to easily obtain the missing information. "
                "Address the attorneys directly."
            )

            first_gap = gaps[0]
            field = first_gap.get('field', 'unknown')
            reason = first_gap.get('reason', 'Missing information.')

            submission_data = getattr(state, "submission", None)
            if submission_data:
                # We format it safely to avoid prompt template issues
                current_submission_context = str(submission_data.model_dump(exclude_none=True)).replace("{", "{{").replace("}", "}}")
            else:
                current_submission_context = "No information extracted yet."

            user_prompt = (
                f"Current Extracted Information Context:\n{current_submission_context}\n\n"
                f"We are missing information for the field '{field}' because: {reason}.\n\n"
                "Please generate one strategic question to ask for this missing information. "
                "Use the Current Extracted Information Context to inform your question and avoid asking for information we already know (like the firm name or practice area if it is already present in the context)."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])

            chain = prompt | structured_llm
            result = chain.invoke({})

            question = result.question

        except Exception as e:
            # Fallback to simple logic if LLM fails (e.g., no API key in tests)
            updates["messages"].append(f"LLM generation failed: {e}. Falling back to simple questions.")
            first_gap = gaps[0]
            field = first_gap.get("field", "unknown")
            question = f"We are missing information for '{field}'. Could you provide details?"

    updates["new_answer"] = {
        "question_text": question,
        "answer": ""
    }
    updates["messages"].append("Interrogator node: Generated 1 question and paused for Laravel.")

    return updates
