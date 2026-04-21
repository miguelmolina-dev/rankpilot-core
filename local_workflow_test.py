import os
import base64
from src.core.workflow import build_workflow
from src.core.state import AgentState, MetaData
from os import getenv
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

def main():
    print("--- RankPilot Local Workflow Test ---")

    # Build the workflow
    workflow = build_workflow()

    # 1. Create a dummy file as if uploaded by the user
    file_path = r"G:\Proyectos_Python\rankpilot-core\tests\FINAL_Chambers 2026_Mexico_Perez Correa_Fintech_Submission (1)(2).docx"
    
    # 2. Read the ACTUAL PDF file so the PDF parser doesn't crash on dummy data
    try:
        with open(file_path, "rb") as docx_file:
            real_docx_content = docx_file.read()
        b64_string = base64.b64encode(real_docx_content).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: Could not find the test document at {file_path}")
        return

    print("\n[Local] Initializing state...")

    # Initial state mimicking what would be sent to initiate
    current_state = AgentState(
        submission_id="test_001",
        # <-- AQUÍ ESTÁ LA MAGIA: Pasamos los 5 requerimientos de Laravel
        metadata=MetaData(
            directory="Legal500", 
            guide="Latin America",
            region="LatAm",
            jurisdiction="Mexico",
            practice_area="Fintech",
            firm_name="Perez Correa"
        ),
        base64_documents=[{"filename": file_path, "base64": b64_string}],
        decoded_file_paths=[],
        target_submission_type="Legal500", # (Legacy, pero lo dejamos)
        submission=None,
        gaps=[],
        questions=[],
        history=[],
        new_answer={"question_text": "", "answer": ""},
        output_base64=None,
        messages=[],
        current_step="init",
        errors=[]
    )

    print("\n[Local] Starting first workflow invocation...")

    # First invocation
    result = workflow.invoke(current_state)
    current_state = result

    # Check messages and gaps
    print("\n[Local] Received state after first invocation.")
    for msg in current_state.get("messages", []):
        print(f"   [Log]: {msg}")

    # Enter the interactive loop
    max_iterations = 8
    iteration = 0
    while current_state.get("gaps") and iteration < max_iterations:
        iteration += 1
        gaps = current_state.get("gaps", [])
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
        print("\n--- Final Document Assembled (Act 2 Complete) ---")

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

    # ==========================================
    # NUEVO: IMPRIMIR EL ACTO 3 (RANKPILOT ENGINE)
    # ==========================================
    print("\n========= 🏆 RANKPILOT STRATEGIC DIAGNOSIS (Act 3) =========")
    
    exec_summary = current_state.get("executive_summary", {})
    if exec_summary:
        print(f"Overall Score:  {exec_summary.get('overall_score', 'N/A')}/100")
        print(f"Risk Level:     {exec_summary.get('risk_level', 'N/A')}")
        print(f"Verdict:        {exec_summary.get('strategic_verdict', 'N/A')}")
        
        print("\n--- Top Differentiators ---")
        for diff in exec_summary.get('top_differentiators', []):
            print(f" - {diff}")

        print("\n--- The Evolution Path (Roadmap) ---")
        evolution_path = current_state.get("evolution_path", [])
        if evolution_path:
            for i, step in enumerate(evolution_path):
                # Soportar Pydantic model o dict
                title = getattr(step, 'action_title', step.get('action_title', '')) if isinstance(step, dict) else step.action_title
                date = getattr(step, 'target_completion_date', step.get('target_completion_date', '')) if isinstance(step, dict) else step.target_completion_date
                print(f"Step {i+1} [{date}]: {title}")
        else:
            print("No Evolution Path generated.")
            
        print("============================================================")

        print("\n--- Final Submission Data (JSON Object) ---")
            
        print("\n--- Formal Audit Letter ---")
        print(exec_summary.get('audit_letter_markdown', 'No letter generated.'))
    else:
        print("Executive Summary not found. The Act 3 pipeline might have failed.")
    
    print("============================================================")

    print("\n--- Final Submission Data (JSON Object) ---")
    # Imprimimos de forma limpia si es un objeto Pydantic
    submission_obj = current_state.get("submission")
    if submission_obj:
        print(submission_obj.model_dump_json(indent=2)[:1500] + "\n... [Truncated for readability]")
    else:
        print("No submission object found.")
    print("-------------------------------------------\n")

if __name__ == "__main__":
    main()