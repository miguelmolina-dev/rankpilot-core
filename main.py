from fastapi import FastAPI, Request
from core.graph import app as graph_app 
from langchain_core.messages import HumanMessage
import uuid

# Instancia de FastAPI que buscará Uvicorn
api = FastAPI()

def run_rankpilot(user_input: str, thread_id: str, is_file: bool = False):
    """
    Motor principal del sistema RankPilot. 
    Esta función es el puente entre la API y el Grafo de Agentes.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    if is_file:
        # Flujo de Ingestión de Documentos
        initial_state = {"file_path": user_input, "messages": []}
        return graph_app.invoke(initial_state, config)
    else:
        # Flujo de Interacción por Texto/Chat
        return graph_app.invoke(
            {"messages": [HumanMessage(content=user_input)]}, 
            config
        )

@api.post("/process")
async def process_request(request: Request):
    """
    Endpoint que recibe las peticiones de Laravel.
    """
    try:
        data = await request.json()
        
        user_input = data.get("user_input")
        # Si Laravel no manda thread_id, generamos uno para mantener el estado
        thread_id = data.get("thread_id", str(uuid.uuid4()))
        is_file = data.get("is_file", False)
        
        if not user_input:
            return {"status": "error", "message": "No user_input provided"}

        result = run_rankpilot(user_input, thread_id, is_file)
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}    
