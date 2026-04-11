from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
from src.core.workflow import build_workflow
from src.core.state import AgentState

api = FastAPI(title="RankPilot API")

class ProcessRequest(BaseModel):
    base64_documents: List[Dict[str, str]]
    submission_type: Optional[str] = "Legal500"

@api.get("/")
def read_root():
    return {"message": "Welcome to RankPilot API"}

@api.post("/process")
def process_documents(request: ProcessRequest):
    workflow = build_workflow()

    initial_state: AgentState = {
        "base64_documents": request.base64_documents,
        "decoded_file_paths": [],
        "submission_type": request.submission_type,
        "submission": None,
        "gaps": [],
        "questions": [],
        "output_base64": None,
        "messages": [],
        "current_step": "init",
        "errors": []
    }

    result = workflow.invoke(initial_state)

    return {
        "output_base64": result.get("output_base64"),
        "messages": result.get("messages"),
        "current_step": result.get("current_step"),
        "gaps": result.get("gaps"),
        "questions": result.get("questions")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)
