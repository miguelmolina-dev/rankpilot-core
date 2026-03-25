from core.graph import app
from core.state import AgentState
from langchain_core.messages import HumanMessage
import uuid

def run_rankpilot(user_input: str, thread_id: str, is_file: bool = False):
    """
    Main execution wrapper for the RankPilot Multi-Agent System.
    
    Args:
        user_input: Either the file path (if is_file=True) or the chat message.
        thread_id: The Laravel session ID for persistence.
        is_file: Boolean flag to determine the entry point.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    if is_file:
        # Initial Ingestion
        print(f"--- [STARTING NEW CASE: {thread_id}] ---")
        initial_state = {"file_path": user_input, "messages": []}
        output = app.invoke(initial_state, config)
    else:
        # Dialectic Response
        print(f"--- [RESUMING CASE: {thread_id}] ---")
        output = app.invoke(
            {"messages": [HumanMessage(content=user_input)]}, 
            config
        )
    
    return output

# --- TEST SCENARIO ---
if __name__ == "__main__":
    session_id = str(uuid.uuid4()) # Simulate Laravel Session
    
    # Step 1: User uploads the Pérez Correa file
    result = run_rankpilot("uploads/perez_correa.docx", session_id, is_file=True)
    
    # Step 2: Check if we are in Interrogation or Writing
    if result["current_step"] == "waiting_for_user":
        print("\nAGENT SAYS:\n", result["messages"][-1].content)
        
        # Step 3: Simulate User providing the missing strategic info
        user_answer = "The restructuring matter involved 4 jurisdictions and $500M in distressed debt."
        final_result = run_rankpilot(user_answer, session_id, is_file=False)
        
        if final_result["is_complete"]:
            print("\nSUCCESS: LaTeX Generated.")
            # print(final_result["latex_code"])