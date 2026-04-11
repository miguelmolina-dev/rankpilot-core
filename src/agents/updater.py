from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import Legal500Submission, BaseSubmission

def update_node(state: AgentState) -> dict:
    """
    Update Node:
    Receives an incoming state with a user answer in new_answer["answer"].
    Merges the answer into the existing submission schema.
    Appends the Q&A pair to the history, and clears the new_answer.
    """
    updates = {"current_step": "update", "messages": []}

    new_answer_dict = state.get("new_answer", {})
    question_text = new_answer_dict.get("question_text", "")
    answer_text = new_answer_dict.get("answer", "")

    # Keep existing history if missing
    history = state.get("history", [])

    if answer_text:
        # Append to history
        qa_pair = f"Q_Text: {question_text} | Answer: {answer_text}"
        history.append(qa_pair)
        updates["history"] = history

        updates["messages"].append(f"Update node: Received answer for '{question_text}'")

        # Now, update the submission based on the new answer.
        # We'll use LLM to map the answer into the submission schema.
        submission_data = state.get("submission")
        submission_type = state.get("submission_type", "Legal500")

        if submission_data:
            current_submission_dict = submission_data.model_dump()
        else:
            current_submission_dict = {}

        try:
            llm = get_llm(temperature=0.0)

            # Determine the structured output type based on the submission type.
            # Currently only Legal500Submission is fully defined in schemas for usage here.
            # We will default to Legal500Submission if not recognized or mapped.
            if submission_type == "Legal500":
                structured_llm = llm.with_structured_output(Legal500Submission)
            else:
                structured_llm = llm.with_structured_output(Legal500Submission)

            system_prompt = (
                "You are an expert legal data extraction assistant. "
                "You are given the current state of a legal submission document, along with a newly answered question. "
                "Update the submission document by filling the missing fields that the answer provides. "
                "Maintain all previously filled data. Ensure your output perfectly matches the requested schema."
            )

            user_prompt = (
                f"Current Submission Data:\n{current_submission_dict}\n\n"
                f"Newly Answered Question:\nQuestion: {question_text}\nAnswer: {answer_text}\n\n"
                "Please provide the updated full submission object with the new information incorporated."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])

            chain = prompt | structured_llm
            updated_submission = chain.invoke({})

            updates["submission"] = updated_submission

        except Exception as e:
            updates["messages"].append(f"LLM update failed: {e}. The submission was not updated with the new answer.")

    # Always clear the new_answer dictionary
    updates["new_answer"] = {"question_text": "", "answer": ""}

    return updates
