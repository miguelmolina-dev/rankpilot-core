from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
from src.core.workflow import build_workflow
from src.core.state import AgentState

api = FastAPI(title="RankPilot API")

from src.core.schemas import BaseSubmission
from typing import Any

class ProcessRequest(BaseModel):
    base64_documents: List[Dict[str, str]] = []
    decoded_file_paths: List[str] = []
    target_submission_type: Optional[str] = "Legal500"
    input_document_type: Optional[str] = None
    submission: Optional[Dict[str, Any]] = None
    gaps: List[Dict[str, Any]] = []
    questions: List[str] = []
    history: List[str] = []
    new_answer: Dict[str, str] = {"question_text": "", "answer": ""}
    output_base64: Optional[str] = None
    messages: List[str] = []
    current_step: str = "init"
    errors: List[str] = []

@api.get("/")
def read_root():
    return {"message": "Welcome to RankPilot API"}

@api.post("/process")
def process_documents(request: ProcessRequest):
    workflow = build_workflow()

    # We load the submission dict into the Pydantic model if it exists
    from src.core.schemas import AnchorSubmission

    sub_model = None
    if request.submission:
        sub_model = AnchorSubmission(**request.submission)

    initial_state: AgentState = {
        "base64_documents": request.base64_documents,
        "decoded_file_paths": request.decoded_file_paths,
        "target_submission_type": request.target_submission_type,
        "input_document_type": request.input_document_type,
        "submission": sub_model,
        "gaps": request.gaps,
        "questions": request.questions,
        "history": request.history,
        "new_answer": request.new_answer,
        "output_base64": request.output_base64,
        "messages": request.messages,
        "current_step": request.current_step,
        "errors": request.errors
    }

    result = workflow.invoke(initial_state)

    sub = result.get("submission")
    sub_dict = sub.model_dump() if sub else None

    return {
        "base64_documents": result.get("base64_documents", []),
        "decoded_file_paths": result.get("decoded_file_paths", []),
        "target_submission_type": result.get("target_submission_type"),
        "input_document_type": result.get("input_document_type"),
        "submission": sub_dict,
        "gaps": result.get("gaps", []),
        "questions": result.get("questions", []),
        "history": result.get("history", []),
        "new_answer": result.get("new_answer", {}),
        "output_base64": result.get("output_base64"),
        "messages": result.get("messages", []),
        "current_step": result.get("current_step", ""),
        "errors": result.get("errors", [])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)
