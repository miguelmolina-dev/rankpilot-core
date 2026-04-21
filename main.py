from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import traceback
import uuid
import sys
from src.core.workflow import build_workflow
from src.core.state import AgentState, MetaData
from src.core.schemas import Legal500Submission, ChambersSubmission

api = FastAPI(title="RankPilot API")

# --- BASE DE DATOS EN MEMORIA (Para el Polling) ---
# Almacena el progreso de los trabajos. (En producción masiva se cambiaría por Redis)
JOBS_DB = {}

# 1. Estructura del Payload
class AgentStatePayload(BaseModel):
    submission_id: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = None # ¡Clave para el Acto 1!
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
    new_answer: Dict[str, Any] = {"target_field": "", "question_text": "", "answer": ""}
    output_base64: Optional[str] = None
    messages: List[str] = []
    current_step: str = ""
    errors: List[str] = []

# --- 2. EL WORKER EN SEGUNDO PLANO (La magia de LangGraph) ---
def run_workflow_task(job_id: str, initial_state: dict, config: dict):
    try:
        workflow = build_workflow()
        JOBS_DB[job_id]["status"] = "processing"
        
        # Mapeo visual de progreso basado en los nodos de LangGraph
        progress_map = {
            "preparation": {"p": 10, "msg": "Extracting text from document..."},
            "ingestion": {"p": 30, "msg": "Mapping data to AI schema..."},
            "sanitizer": {"p": 60, "msg": "Sanitizing and rewriting fields..."},
            "audit": {"p": 80, "msg": "Auditing submission for gaps..."},
            "interrogator": {"p": 100, "msg": "Audit complete. Ready for Q&A."},
            "optimizer": {"p": 40, "msg": "Optimizing strategic narrative..."},
            "snapshot_generator": {"p": 60, "msg": "Generating audit snapshot..."},
            "scheduler": {"p": 80, "msg": "Building roadmap timeline..."},
            "executive_writer": {"p": 95, "msg": "Drafting executive letter..."},
            "assembly": {"p": 100, "msg": "Assembling final document."}
        }

        # Ejecutamos con .stream() para ir nodo por nodo
        final_state = initial_state
        for output in workflow.stream(initial_state, config):
            for node_name, state_update in output.items():
                # Acumulamos el estado
                final_state.update(state_update)
                
                # Actualizamos el porcentaje visual para Laravel
                if node_name in progress_map:
                    JOBS_DB[job_id]["progress"] = progress_map[node_name]["p"]
                    JOBS_DB[job_id]["message"] = progress_map[node_name]["msg"]
                else:
                    JOBS_DB[job_id]["message"] = f"Processing {node_name}..."

        # Al terminar, preparamos el JSON final para enviar a Laravel
        sub = final_state.get("submission")
        sub_dict = sub.model_dump() if hasattr(sub, 'model_dump') else None
        
        # Opcional: Extraer el Executive Summary si existe (Acto 3)
        exec_summary = final_state.get("executive_summary")
        exec_summary_dict = exec_summary.model_dump() if hasattr(exec_summary, 'model_dump') else exec_summary

        final_agent_state = {
            "metadata": final_state.get("metadata", {}),
            "submission": sub_dict,
            "gaps": final_state.get("gaps", []),
            "dismissed_gaps": final_state.get("dismissed_gaps", []),
            "questions": final_state.get("questions", []),
            "new_answer": {"target_field": "", "question_text": "", "answer": ""},
            "output_base64": final_state.get("output_base64"),
            "evolution_path": final_state.get("evolution_path", []),
            "executive_summary": exec_summary_dict,
            "errors": final_state.get("errors", [])
        }

        JOBS_DB[job_id]["progress"] = 100
        JOBS_DB[job_id]["status"] = "completed"
        JOBS_DB[job_id]["data"] = final_agent_state

    except Exception as e:
        print(f"CRITICAL WORKER ERROR: {str(e)}")
        traceback.print_exc()
        JOBS_DB[job_id]["status"] = "failed"
        JOBS_DB[job_id]["message"] = f"Error: {str(e)}"
        JOBS_DB[job_id]["error_details"] = traceback.format_exc()

# --- 3. ENDPOINT INICIAL: Dispara el proceso ---
@api.post("/process")
async def process_documents(request: Request, background_tasks: BackgroundTasks):
    try:
        raw_data = await request.json()
        thread_id = raw_data.get("thread_id", str(uuid.uuid4()))
        state_data = raw_data.get("agent_state", {})
        
        # Limpieza de basura PHP
        submission_data = state_data.get("submission", {})
        if isinstance(submission_data, dict):
            buggy_fields = ["narratives", "individual_nominations", "team_dynamics"]
            for field in buggy_fields:
                val = submission_data.get(field)
                if isinstance(val, dict) and ("stdClass" in val or not val):
                    submission_data[field] = {}
                elif val is None:
                    submission_data[field] = {}

        state_input = AgentStatePayload(**state_data)
        
        sub_model = None
        if submission_data:
            target = state_input.target_submission_type
            if target == "Legal500":
                sub_model = Legal500Submission(**submission_data)
            elif target in ["Chambers", "Chambers and Partners"]:
                sub_model = ChambersSubmission(**submission_data)
                
        # Parseo de Metadata
        meta_obj = MetaData(**state_input.metadata) if state_input.metadata else None

        initial_state = {
            "submission_id": state_input.submission_id,
            "metadata": meta_obj,
            "base64_documents": state_input.base64_documents,
            "target_submission_type": state_input.target_submission_type,
            "submission": sub_model,
            "gaps": state_input.gaps,
            "dismissed_gaps": state_input.dismissed_gaps,
            "new_answer": state_input.new_answer,
            "errors": state_input.errors
        }
        config = {"configurable": {"thread_id": thread_id}}

        # Creamos el Job
        job_id = str(uuid.uuid4())
        JOBS_DB[job_id] = {
            "status": "started", 
            "progress": 0, 
            "message": "Initializing...", 
            "data": None
        }

        # Despachamos al fondo
        background_tasks.add_task(run_workflow_task, job_id, initial_state, config)

        # Devolvemos INMEDIATAMENTE
        return {"job_id": job_id, "status": "started", "thread_id": thread_id}

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "failed", "error": str(e)})

# --- 4. ENDPOINT DE POLLING: Laravel pregunta por este ---
@api.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in JOBS_DB:
        return JSONResponse(status_code=404, content={"error": "Job not found or expired."})
    return JOBS_DB[job_id]