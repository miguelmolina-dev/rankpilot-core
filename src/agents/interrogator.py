from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm

class StrategicQuestions(BaseModel):
    questions: List[str] = Field(
        description="A list of strategic questions asking for the missing information."
    )

def interrogator_node(state: AgentState) -> dict:
    """
    Interrogator Node:
    Generates dynamic, strategic questions for the fields marked as null or missing (gaps)
    using an LLM.
    """
    updates = {"current_step": "interrogator", "messages": []}

    gaps = state.get("gaps", [])
    questions = []

    if gaps:
        try:
            llm = get_llm(temperature=0.2)
            structured_llm = llm.with_structured_output(StrategicQuestions)

            system_prompt = (
                "You are an expert legal ranking strategist advising a law firm. "
                "The firm is preparing a submission for legal directories (like Chambers or Legal500), "
                "but some required fields are missing. "
                "Generate a set of clear, professional, and strategic questions to ask the attorneys "
                "to easily obtain the missing information. "
                "Address the attorneys directly."
            )

            gaps_text = "\n".join([
                f"- Field: {gap.get('field', 'unknown')}. Reason: {gap.get('reason', 'Missing information.')}"
                for gap in gaps
            ])

            user_prompt = (
                "Here are the missing fields and the reasons they are flagged as missing:\n"
                f"{gaps_text}\n\n"
                "Please generate the strategic questions to ask for this missing information."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])

            chain = prompt | structured_llm
            result = chain.invoke({})

            questions = result.questions

        except Exception as e:
            # Fallback to simple logic if LLM fails (e.g., no API key in tests)
            updates["messages"].append(f"LLM generation failed: {e}. Falling back to simple questions.")
            for gap in gaps:
                field = gap.get("field", "unknown")
                questions.append(f"We are missing information for '{field}'. Could you provide details?")

    updates["questions"] = questions
    updates["messages"].append(f"Interrogator node: Generated {len(questions)} questions.")

    return updates
