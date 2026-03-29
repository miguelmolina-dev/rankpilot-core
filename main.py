import os
import uuid
import logging
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from core.graph import app as graph_app 
from langchain_core.messages import HumanMessage

# Configuración de Logs para ver errores en la consola de Ubuntu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = FastAPI(title="RankPilot AI Core", version="1.1.0")

# 1. Definición del Esquema de Entrada (Pydantic)
# Esto soluciona el problema de False/false y llaves faltantes automáticamente.
class ProcessRequest(BaseModel):
    user_input: str
    thread_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    is_file: bool = False
    metadata: Optional[Dict[str, Any]] = {}

# 2. Endpoint de Salud (Señales de Vida)
@api.get("/health")
async def health_check():
    return {"status": "online", "message": "RankPilot Core is alive"}

def run_rankpilot(req: ProcessRequest):
    """
    Orquestador con Inyección de Estado Seguro.
    """
    config = {"configurable": {"thread_id": req.thread_id}}
    
    # Construcción del estado inicial asegurando que TODAS las llaves existan
    # Esto evita que el Grafo explote por llaves inexistentes.
    initial_state = {
        "file_path": req.user_input if req.is_file else None,
        "is_file": req.is_file,
        "messages": [HumanMessage(content=req.user_input)] if not req.is_file else [],
        "metadata": req.metadata,
        "is_complete": False,
        "doc_text": None
    }
    
    try:
        # Ejecución del Grafo
        output = graph_app.invoke(initial_state, config)
        return output
    except Exception as e:
        logger.error(f"Error crítico en la ejecución del Grafo: {e}")
        raise ValueError(f"Graph Execution Error: {str(e)}")

# 3. Endpoint de Procesamiento con Validación Automática
@api.post("/process")
async def process_request(req: ProcessRequest):
    try:
        logger.info(f"--- Procesando Thread: {req.thread_id} ---")
        
        result = run_rankpilot(req)
        
        # Resolución de archivos
        pdf_url = result.get("pdf_url")
        if pdf_url and os.path.exists(pdf_url):
            pdf_url = os.path.abspath(pdf_url)

        return {
            "status": "completed" if result.get("is_complete") else "interrogating",
            "thread_id": req.thread_id,
            "data": {
                "pdf_url": pdf_url,
                "is_complete": result.get("is_complete", False),
                "response": result["messages"][-1].content if result.get("messages") else "No response."
            }
        }
    except Exception as e:
        # En lugar de un 500 genérico, devolvemos un 400 o 500 con el error real
        logger.error(f"Error en el endpoint /process: {e}")
        raise HTTPException(status_code=500, detail=str(e))