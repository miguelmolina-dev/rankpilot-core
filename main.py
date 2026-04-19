from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import traceback
import sys
from src.core.workflow import build_workflow
from src.core.state import AgentState
from src.core.schemas import Legal500Submission, ChambersSubmission

api = FastAPI(title="RankPilot API")

# 1. Estructura interna
class AgentStatePayload(BaseModel):
    base64_documents: List[Dict[str, str]] = []
    decoded_file_paths: List[str] = []
    raw_input_text: str = ""
    target_submission_type: Optional[str] = "Legal500"
    input_document_type: Optional[str] = None
    submission: Optional[Dict[str, Any]] = None
    gaps: List[Dict[str, Any]] = []
    dismissed_gaps: List[str] = []
    questions: List[str] = []
    history: List[str] = []
    new_answer: Dict[str, Any] = {"target_field": None, "question_text": None, "answer": None}
    output_base64: Optional[str] = None
    messages: List[str] = []
    current_step: str = ""
    errors: List[str] = []

class ProcessRequest(BaseModel):
    thread_id: str
    agent_state: AgentStatePayload

@api.post("/process")
async def process_documents(request: Request):
    try:
        # 1. Recibimos el JSON crudo
        raw_data = await request.json()
        thread_id = raw_data.get("thread_id", "unknown")
        state_data = raw_data.get("agent_state", {})
        submission_data = state_data.get("submission", {})

        # 2. EL PURIFICADOR: Limpiamos la basura de PHP manualmente
        if isinstance(submission_data, dict):
            buggy_fields = ["narratives", "individual_nominations", "team_dynamics"]
            for field in buggy_fields:
                val = submission_data.get(field)
                # Si es un dict con "stdClass" o si es un dict vacío pero PHP lo mandó mal
                if isinstance(val, dict) and ("stdClass" in val or not val):
                    submission_data[field] = {}
                elif val is None:
                    submission_data[field] = {}

        # 3. Validamos el resto con el modelo (sin que explote por stdClass)
        state_input = AgentStatePayload(**state_data)
        workflow = build_workflow()

        # 4. Mapeo a modelos específicos
        sub_model = None
        if submission_data:
            target = state_input.target_submission_type
            # Cambiamos "Chambers" por "Chambers and Partners" para que coincida con tus logs
            if target == "Legal500":
                sub_model = Legal500Submission(**submission_data)
            elif target in ["Chambers", "Chambers and Partners"]:
                sub_model = ChambersSubmission(**submission_data)

        # 5. Estado para LangGraph
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

        config = {"configurable": {"thread_id": thread_id}}
        result = workflow.invoke(initial_state, config)

        # 6. Serialización de vuelta
        sub = result.get("submission")
        sub_dict = sub.model_dump() if hasattr(sub, 'model_dump') else None

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

        return {
            "status": "success",
            "thread_id": thread_id,
            "agent_state": final_agent_state
        }

    except Exception as e:
        # SI EXPLOTA, TE DEVUELVE EL ERROR REAL EN EL LOG DE LARAVEL
        print(f"CRITICAL API ERROR: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )