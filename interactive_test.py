import os
import requests
from src.io.base64_encoder import encode_file_to_base64

API_BASE_URL = "http://localhost:8000"

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
    print("--- RankPilot Interactive API Simulation ---")
    try:
        filepath = input("Enter the path to the document to process (e.g., test.pdf): ").strip()
    except EOFError:
        print("EOF encountered. Using default mock path.")
        filepath = "test.pdf"

    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} does not exist. Creating a dummy file.")
        with open(filepath, "wb") as f:
            f.write(b"Dummy PDF content")

    print(f"Encoding {filepath} to base64...")
    b64_string = encode_file_to_base64(filepath)
    if not b64_string:
        print("Failed to encode file.")
        return

    print(f"\nSending POST request to {API_BASE_URL}/process ...")
    try:
        response = requests.post(f"{API_BASE_URL}/process", json={
            "filename": os.path.basename(filepath),
            "base64": b64_string
        })
        response.raise_for_status()
        process_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        print("Make sure the API server is running on localhost:8000")
        return

    print("Response received.")

    status = process_data.get("status")
    thread_id = process_data.get("thread_id")
    gaps = process_data.get("gaps", [])

    if status == "interrupted" and gaps:
        print(f"\nWorkflow interrupted. Thread ID: {thread_id}")
        answers = batch_answer_questions(gaps)

        print(f"Sending POST request to {API_BASE_URL}/resume ...")
        try:
            resume_response = requests.post(f"{API_BASE_URL}/resume", json={
                "thread_id": thread_id,
                "answers": answers
            })
            resume_response.raise_for_status()
            resume_data = resume_response.json()
        except requests.exceptions.RequestException as e:
            print(f"API resume request failed: {e}")
            return

        print("Resume response received.")
    else:
        print("\nWorkflow completed without interruptions.")
        resume_data = process_data

    final_base64 = resume_data.get("final_base64")
    if final_base64:
        print("\n--- Final Base64 Output from API ---")
        print(f"Base64 string (truncated): {final_base64[:100]}...{final_base64[-100:]}")
        print("------------------------------------\n")
    else:
        print("\nNo final base64 string returned from the API.")

if __name__ == "__main__":
    main()
