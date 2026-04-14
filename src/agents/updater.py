from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import AnchorSubmission, Legal500Submission

def update_node(state: AgentState) -> dict:
    """
    Update Node:
    Receives an incoming state with a user answer in new_answer["answer"].
    Merges the answer into the existing submission schema.
    Appends the Q&A pair to the history, and clears the new_answer.
    """
    updates = {"current_step": "update", "messages": []}

    new_answer_dict = getattr(state, "new_answer", {}) or {}
    question_text = new_answer_dict.get("question_text", "")
    answer_text = new_answer_dict.get("answer", "")

    # Keep existing history if missing
    history = getattr(state, "history", []) or []

    if answer_text:
        # Append to history
        qa_pair = f"Q_Text: {question_text} | Answer: {answer_text}"
        history.append(qa_pair)
        updates["history"] = history

        updates["messages"].append(f"Update node: Received answer for '{question_text}'")

        # Now, update the submission based on the new answer.
        # We'll use LLM to map the answer into the submission schema.
        submission_data = getattr(state, "submission", None)
        target_submission_type = getattr(state, "target_submission_type", "Legal500") or "Legal500"

        if submission_data:
            current_submission_dict = submission_data.model_dump()
        else:
            current_submission_dict = {}

        try:
            llm = get_llm(temperature=0.0)

            # Determine the structured output type based on the submission type.
            if target_submission_type == "Legal500":
                schema_class = Legal500Submission
            else:
                schema_class = AnchorSubmission

            structured_llm = llm.with_structured_output(schema_class, include_raw=True)

            system_prompt = (
                "You are an expert legal data extraction assistant. "
                "You are given the current state of a legal submission document, along with a newly answered question. "
                "Update the submission document by filling the missing fields that the user's answer provides. "
                "CRITICAL INSTRUCTIONS:\n"
                "1. VERY IMPORTANT: Users may not understand exactly what field they are answering for. "
                "   If the user's answer contains information that logically belongs in other fields "
                "   (e.g., they provide client details when asked about department info), YOU MUST capture that data "
                "   and map it to the correct, relevant fields in the schema.\n"
                "2. Maintain all previously filled data from the 'Current Submission Data'. "
                "3. Use the schema field descriptions to guide your mapping. Be highly resilient to 'dummy' or conversational user input.\n"
                "4. Ensure your output perfectly matches the requested schema structure."
            )

            # Use formatting safely since ChatPromptTemplate expects variables if not escaped
            user_prompt = (
                f"Current Submission Data:\n{current_submission_dict}\n\n"
                f"Question Asked to User:\n{question_text}\n\n"
                f"User's Answer:\n{answer_text}\n\n"
                "Please provide the updated full submission object. Read the user's answer carefully and incorporate ANY relevant information it contains into the appropriate fields in the schema, while preserving all existing data."
            ).replace("{", "{{").replace("}", "}}")

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])

            chain = prompt | structured_llm
            output = chain.invoke({})

            updated_submission = output.get("parsed")
            if not updated_submission:
                raise ValueError("Structured LLM returned empty data or failed to parse. Details: " + str(output.get("parsing_error")))

            updates["submission"] = updated_submission

        except Exception as e:
            updates["messages"].append(f"LLM update failed: {e}. The submission was not updated with the new answer.")

    # Always clear the new_answer dictionary
    updates["new_answer"] = {"question_text": "", "answer": ""}

    return updates
