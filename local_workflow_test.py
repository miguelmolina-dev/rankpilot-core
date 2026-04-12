import os
import base64
from src.core.workflow import build_workflow
from src.core.state import AgentState
from os import getenv
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

def main():
    print("--- RankPilot Local Workflow Test ---")

    # Build the workflow
    workflow = build_workflow()

    # 1. Create a dummy file as if uploaded by the user
    file_path = r"G:\Proyectos_Python\rankpilot-core\tests\FINAL_Chambers 2026_Mexico_Perez Correa_Fintech_Submission (1)(2).pdf"
    
    # 2. Read the ACTUAL PDF file so the PDF parser doesn't crash on dummy data
    try:
        with open(file_path, "rb") as pdf_file:
            real_pdf_content = pdf_file.read()
        b64_string = base64.b64encode(real_pdf_content).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: Could not find the test PDF at {file_path}")
        return

    print("\n[Local] Initializing state...")

    # Initial state mimicking what would be sent to initiate
    current_state: AgentState = {
        "base64_documents": [{"filename": file_path, "base64": b64_string}],
        "decoded_file_paths": [],
        "submission_type": "Legal500",
        "submission": None,
        "gaps": [],
        "questions": [],
        "history": [],
        "new_answer": {"question_text": "", "answer": ""},
        "output_base64": None,
        "messages": [],
        "current_step": "init",
        "errors": []
    }

    print("\n[Local] Starting first workflow invocation...")

    # First invocation
    result = workflow.invoke(current_state)
    current_state = result

    # Check messages and gaps
    print("\n[Local] Received state after first invocation.")
    for msg in current_state.get("messages", []):
        print(f"   [Log]: {msg}")

    # Enter the interactive loop
    max_iterations = 4
    iteration = 0
    while current_state.get("gaps") and iteration < max_iterations:
        iteration += 1
        gaps = current_state.get("gaps")
        print(f"\n[Local] Remaining Gaps: {len(gaps)} (Iteration {iteration}/{max_iterations})")

        new_answer = current_state.get("new_answer", {})
        question_text = new_answer.get("question_text")

        if question_text:
            print(f"\n--- Question from Agent ---")
            print(f"Q: {question_text}")

            try:
                answer = input("Your answer (or press Enter to skip/mock): ")
                if not answer.strip():
                    answer = "Mocked default answer to clear the gap."
            except EOFError:
                print("EOF reached. Mocking answer.")
                answer = "Mocked default answer to clear the gap."

            print(f"---------------------------\n")

            # Update the state with the new answer
            # We copy the state and just update new_answer and clear messages
            current_state["new_answer"]["answer"] = answer
            current_state["messages"] = []

            print("[Local] Invoking workflow with new answer...")

            result = workflow.invoke(current_state)
            current_state = result

            print("\n[Local] Received state after invocation.")
            for msg in current_state.get("messages", []):
                print(f"   [Log]: {msg}")
        else:
            print("Gaps exist but no question was generated. Exiting loop.")
            break

    if iteration >= max_iterations:
        print("\n[Local] Reached maximum iterations. Exiting loop.")
    else:
        print("\n[Local] No more gaps detected.")

    output_b64 = current_state.get("output_base64")
    if output_b64:
        print("\n--- Final Document Assembled ---")

        # Decode base64 and save as docx
        output_dir = os.path.join("data", "processed")
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, "final_submission.docx")

        with open(output_filepath, "wb") as f:
            f.write(base64.b64decode(output_b64))

        print(f"Document successfully saved to: {output_filepath}")
        print("--------------------------------")
    else:
        print("\nNo output base64 found in the final state. Assembly might have failed.")

    print("\n--- Final Submission Data ---")
    print(current_state.get("submission"))
    print("-----------------------------\n")

if __name__ == "__main__":
    main()
