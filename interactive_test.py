import os
import base64
from langgraph.checkpoint.memory import MemorySaver
from src.core.workflow import build_workflow
from src.core.state import AgentState
from src.io.base64_encoder import encode_file_to_base64
from src.core.schemas import Legal500Submission

def batch_answer_questions(gaps):
    answers = {}
    print("\n--- Batch Answering Questions ---")
    for gap in gaps:
        field = gap.get("field")
        reason = gap.get("reason", "Missing field")
        print(f"\nGap: {field} ({reason})")
        # In a real interactive session, you'd use input():
        # answer = input(f"Please provide value for {field}: ")
        # For this interactive test which might be run automatically, we'll mock input if not a tty,
        # but the prompt asked for "interactive test file ... prompt the user". We'll use input().
        try:
            answer = input(f"Please provide value for {field} (or press Enter to skip): ")
            if answer.strip():
                answers[field] = answer.strip()
        except EOFError:
            print("EOF reached. Mocking answer.")
            answers[field] = "Mocked answer"

    print("---------------------------------\n")
    return answers


def main():
    print("Initializing workflow with checkpointer...")
    memory = MemorySaver()
    workflow = build_workflow(checkpointer=memory, interrupt_before=["assembly_node"])

    # Initialize state
    dummy_content = b"Dummy PDF content"
    b64_string = base64.b64encode(dummy_content).decode('utf-8')

    initial_state: AgentState = {
        "base64_documents": [{"filename": "test.pdf", "base64": b64_string}],
        "decoded_file_paths": [],
        "submission_type": "Legal500",
        "submission": None,
        "gaps": [],
        "questions": [],
        "messages": [],
        "current_step": "init",
        "errors": []
    }

    config = {"configurable": {"thread_id": "test_thread"}}

    print("Running workflow...")
    for event in workflow.stream(initial_state, config=config):
        for k, v in event.items():
            print(f"Executed node: {k}")

    # Check state after interruption
    current_state = workflow.get_state(config)
    state_values = current_state.values

    gaps = state_values.get("gaps", [])
    if gaps:
        answers = batch_answer_questions(gaps)

        # In a real scenario we'd use the answers to update the submission.
        # Let's mock the update to clear gaps so it proceeds to assembly.
        print("Updating state to clear gaps...")
        workflow.update_state(config, {"gaps": []})

        print("Resuming workflow...")
        for event in workflow.stream(None, config=config):
            for k, v in event.items():
                print(f"Executed node: {k}")
    else:
        print("No gaps found, workflow finished.")

    # Base64 Render final document
    print("\n--- Final Base64 Output ---")
    processed_dir = "data/processed"
    if os.path.exists(processed_dir):
        files = os.listdir(processed_dir)
        docx_files = [f for f in files if f.endswith(".docx")]
        if docx_files:
            # Get the most recently created docx
            latest_file = max(docx_files, key=lambda f: os.path.getctime(os.path.join(processed_dir, f)))
            filepath = os.path.join(processed_dir, latest_file)
            print(f"Encoding file: {filepath}")
            b64_output = encode_file_to_base64(filepath)
            if b64_output:
                # Print only first 100 and last 100 chars to avoid flooding the console
                print(f"Base64 string (truncated): {b64_output[:100]}...{b64_output[-100:]}")
            else:
                print("Failed to encode base64.")
        else:
            print("No .docx files found in data/processed")
    else:
        print(f"Directory {processed_dir} does not exist.")
    print("---------------------------\n")

if __name__ == "__main__":
    main()
