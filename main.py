from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from src.core.workflow import build_workflow
from src.core.state import AgentState
from src.core.schemas import Legal500Submission, ChambersSubmission

api = FastAPI(title="RankPilot API")

# 1. Definimos la estructura interna del estado
class AgentStatePayload(BaseModel):
    base64_documents: List[Dict[str, str]] = []
    decoded_file_paths: List[str] = []
    raw_input_text: str = ""  # Agregado
    target_submission_type: Optional[str] = "Legal500"
    input_document_type: Optional[str] = None
    submission: Optional[Dict[str, Any]] = None
    gaps: List[Dict[str, Any]] = []
    dismissed_gaps: List[str] = []  # Agregado
    questions: List[str] = []
    history: List[str] = []
    new_answer: Dict[str, Any] = {"target_field": None, "question_text": None, "answer": None}
    output_base64: Optional[str] = None
    messages: List[str] = []
    current_step: str = ""
    errors: List[str] = []

# 2. EL WRAPPER: Definimos cómo Laravel envía los datos (El fix principal)
class ProcessRequest(BaseModel):
    thread_id: str
    agent_state: AgentStatePayload

@api.get("/")
def read_root():
    return {"message": "Welcome to RankPilot API"}

@api.post("/process")
def process_documents(request: ProcessRequest):
    workflow = build_workflow()

    # Extraemos el estado y el hilo del request envuelto
    thread_id = request.thread_id
    state_input = request.agent_state

    # Cargamos el diccionario de submission al modelo de Pydantic correspondiente
    sub_model = None
    if state_input.submission:
        if state_input.target_submission_type == "Legal500":
            sub_model = Legal500Submission(**state_input.submission)
        elif state_input.target_submission_type == "Chambers":
            sub_model = ChambersSubmission(**state_input.submission)

    # Construimos el estado inicial para LangGraph
    initial_state: AgentState = {
        "base64_documents": state_input.base64_documents,
        "decoded_file_paths": state_input.decoded_file_paths,
        "raw_input_text": state_input.raw_input_text,
        "target_submission_type": state_input.target_submission_type,
        "input_document_type": state_input.input_document_type,
        "submission": sub_model,
        "gaps": state_input.gaps,
        "dismissed_gaps": state_input.dismissed_gaps,
        "questions": state_input.questions,
        "history": state_input.history,
        "new_answer": state_input.new_answer,
        "output_base64": state_input.output_base64,
        "messages": state_input.messages,
        "current_step": state_input.current_step,
        "errors": state_input.errors
    }

    # Configuramos el hilo para LangGraph (si usas persistencia)
    config = {"configurable": {"thread_id": thread_id}}

    # Ejecutamos el grafo pasándole la configuración
    result = workflow.invoke(initial_state, config)

    # Extraemos y serializamos el modelo de Pydantic de vuelta a diccionario
    sub = result.get("submission")
    sub_dict = sub.model_dump() if sub else None

    # Reconstruimos el estado plano para envolverlo en la respuesta
    final_agent_state = {
        "base64_documents": result.get("base64_documents", []),
        "decoded_file_paths": result.get("decoded_file_paths", []),
        "raw_input_text": result.get("raw_input_text", ""),
        "target_submission_type": result.get("target_submission_type"),
        "input_document_type": result.get("input_document_type"),
        "submission": sub_dict,
        "gaps": result.get("gaps", []),
        "dismissed_gaps": result.get("dismissed_gaps", []),
        "questions": result.get("questions", []),
        "history": result.get("history", []),
        "new_answer": result.get("new_answer", {}),
        "output_base64": result.get("output_base64"),
        "messages": result.get("messages", []),
        "current_step": result.get("current_step", ""),
        "errors": result.get("errors", [])
    }

    # 3. EL RETURN ENVUELTO: Respondemos exactamente como Laravel lo exige
    return {
        "status": "success",
        "thread_id": thread_id,
        "agent_state": final_agent_state
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)
