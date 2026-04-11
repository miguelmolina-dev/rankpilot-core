from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ProcessRequest(BaseModel):
    filename: str
    base64: str

class ResumeRequest(BaseModel):
    thread_id: str
    answers: Dict[str, Any]

class ProcessResponse(BaseModel):
    status: str
    thread_id: Optional[str] = None
    gaps: Optional[List[Dict[str, Any]]] = None
    final_base64: Optional[str] = None

import uuid
from langgraph.checkpoint.memory import MemorySaver
import os
from src.core.workflow import build_workflow
from src.core.state import AgentState
from src.io.base64_encoder import encode_file_to_base64

api = FastAPI(title="RankPilot API")

# Global memory checkpointer for testing/demo purposes
global_memory = MemorySaver()
global_workflow = build_workflow(checkpointer=global_memory, interrupt_before=["assembly_node"])

@api.get("/")
def read_root():
    return {"message": "Welcome to RankPilot API"}

@api.post("/process", response_model=ProcessResponse)
def process_document(request: ProcessRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: AgentState = {
        "base64_documents": [{"filename": request.filename, "base64": request.base64}],
        "decoded_file_paths": [],
        "submission_type": "Legal500",
        "submission": None,
        "gaps": [],
        "questions": [],
        "messages": [],
        "current_step": "init",
        "errors": []
    }

    # Run workflow
    for event in global_workflow.stream(initial_state, config=config):
        pass

    # Check if interrupted
    current_state = global_workflow.get_state(config)
    state_values = current_state.values
    gaps = state_values.get("gaps", [])

    if gaps:
        return ProcessResponse(
            status="interrupted",
            thread_id=thread_id,
            gaps=gaps
        )
    else:
        # If there are no gaps, it would proceed to completion (but we interrupt before assembly)
        # To handle this edge case perfectly we'd need to manually resume. For our use case,
        # we assume gaps exist or we handle resumption in another step.
        return ProcessResponse(status="completed", thread_id=thread_id)

@api.post("/resume", response_model=ProcessResponse)
def resume_document(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    # In a real app we'd inject `request.answers` into the submission state.
    # For now, we clear the gaps to let the workflow proceed.
    global_workflow.update_state(config, {"gaps": []})

    # Resume workflow
    for event in global_workflow.stream(None, config=config):
        pass

    # Get final output docx
    processed_dir = "data/processed"
    final_b64 = None
    if os.path.exists(processed_dir):
        files = os.listdir(processed_dir)
        docx_files = [f for f in files if f.endswith(".docx")]
        if docx_files:
            latest_file = max(docx_files, key=lambda f: os.path.getctime(os.path.join(processed_dir, f)))
            filepath = os.path.join(processed_dir, latest_file)
            final_b64 = encode_file_to_base64(filepath)

    return ProcessResponse(status="completed", thread_id=request.thread_id, final_base64=final_b64)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)
