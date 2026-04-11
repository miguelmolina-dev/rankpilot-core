with open("main.py", "r") as f:
    content = f.read()

content = content.replace(
"""class ProcessRequest(BaseModel):
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
    }""",
"""from src.core.schemas import BaseSubmission
from typing import Any

class ProcessRequest(BaseModel):
    base64_documents: List[Dict[str, str]] = []
    decoded_file_paths: List[str] = []
    submission_type: Optional[str] = "Legal500"
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
    from src.core.schemas import Legal500Submission # assuming Legal500 as default implementation

    sub_model = None
    if request.submission:
        sub_model = Legal500Submission(**request.submission)

    initial_state: AgentState = {
        "base64_documents": request.base64_documents,
        "decoded_file_paths": request.decoded_file_paths,
        "submission_type": request.submission_type,
        "submission": sub_model,
        "gaps": request.gaps,
        "questions": request.questions,
        "history": request.history,
        "new_answer": request.new_answer,
        "output_base64": request.output_base64,
        "messages": request.messages,
        "current_step": request.current_step,
        "errors": request.errors
    }""")

content = content.replace(
"""    result = workflow.invoke(initial_state)

    return {
        "output_base64": result.get("output_base64"),
        "messages": result.get("messages"),
        "current_step": result.get("current_step"),
        "gaps": result.get("gaps"),
        "questions": result.get("questions")
    }""",
"""    result = workflow.invoke(initial_state)

    sub = result.get("submission")
    sub_dict = sub.model_dump() if sub else None

    return {
        "base64_documents": result.get("base64_documents", []),
        "decoded_file_paths": result.get("decoded_file_paths", []),
        "submission_type": result.get("submission_type"),
        "submission": sub_dict,
        "gaps": result.get("gaps", []),
        "questions": result.get("questions", []),
        "history": result.get("history", []),
        "new_answer": result.get("new_answer", {}),
        "output_base64": result.get("output_base64"),
        "messages": result.get("messages", []),
        "current_step": result.get("current_step", ""),
        "errors": result.get("errors", [])
    }""")

with open("main.py", "w") as f:
    f.write(content)
