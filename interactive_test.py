import os
import sys
import argparse
import base64
from fastapi.testclient import TestClient
from main import api

def main():
    parser = argparse.ArgumentParser(description="RankPilot Stateless Frontend Simulation")
    parser.add_argument("filepath", help="Path to the PDF file to upload")
    args = parser.parse_args()

    if not os.path.exists(args.filepath):
        print(f"Error: File not found at {args.filepath}")
        sys.exit(1)

    print("--- RankPilot Stateless Frontend Simulation (Laravel style) ---")

    # Read the file and base64 encode it
    with open(args.filepath, "rb") as f:
        file_content = f.read()
    b64_string = base64.b64encode(file_content).decode('utf-8')
    filename = os.path.basename(args.filepath)

    # Initialize TestClient
    client = TestClient(api)

    print(f"\n[Frontend] Uploading initial document: {filename}...")

    # Initial state mimicking what Laravel would send to initiate
    current_state = {
        "base64_documents": [{"filename": filename, "base64": b64_string}],
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

    # First request
    response = client.post("/process", json=current_state)
    if response.status_code != 200:
        print(f"Error from API: {response.status_code} - {response.text}")
        return

    current_state = response.json()

    # Check messages and gaps
    print("\n[Frontend] Received response from backend.")
    for msg in current_state.get("messages", []):
        print(f"   [Backend Log]: {msg}")

    # Now, enter the interactive loop
    # We continue until there are no more gaps and we have an output base64
    max_iterations = 10
    iteration = 0
    while current_state.get("gaps") and iteration < max_iterations:
        iteration += 1
        gaps = current_state.get("gaps")
        print(f"\n[Frontend] Remaining Gaps: {len(gaps)} (Iteration {iteration}/{max_iterations})")

        # In this workflow, if there are gaps, the backend generates one question at a time
        new_answer = current_state.get("new_answer", {})
        question_text = new_answer.get("question_text")

        if question_text:
            print(f"\n--- Question from Agent ---")
            print(f"Q: {question_text}")

            # Simulate asking user
            try:
                answer = input("Your answer (or press Enter to skip/mock): ")
                if not answer.strip():
                    answer = "Mocked default answer to clear the gap."
            except EOFError:
                print("EOF reached. Mocking answer.")
                answer = "Mocked default answer to clear the gap."

            print(f"---------------------------\n")

            # Set the answer in the state payload
            current_state["new_answer"]["answer"] = answer

            # Send the entire updated state back to the API
            print("[Frontend] Sending updated state back to /process endpoint...")

            # Clear previous messages so we only see new ones
            current_state["messages"] = []

            response = client.post("/process", json=current_state)
            if response.status_code != 200:
                print(f"Error from API: {response.status_code} - {response.text}")
                return

            current_state = response.json()

            print("\n[Frontend] Received updated response.")
            for msg in current_state.get("messages", []):
                print(f"   [Backend Log]: {msg}")
        else:
            # If there are gaps but no question was generated, something might be wrong or it needs a different mechanism
            print("Gaps exist but no question was generated. Exiting loop.")
            break

    if iteration >= max_iterations:
        print("\n[Frontend] Reached maximum iterations. Exiting loop.")
    else:
        print("\n[Frontend] No more gaps detected.")

    output_b64 = current_state.get("output_base64")
    if output_b64:
        print("\n--- Final Document Assembled ---")
        print(f"Base64 Document (truncated): {output_b64[:100]}...{output_b64[-100:]}")
        print("--------------------------------")
    else:
        print("\nNo output base64 found in the final state. Assembly might have failed.")

    print("\n--- Final Submission Data ---")
    print(current_state.get("submission"))
    print("-----------------------------\n")

if __name__ == "__main__":
    main()
