import os
import uuid
from fastapi import FastAPI, Request
from core.graph import app as graph_app 
from langchain_core.messages import HumanMessage

# 1. Instancia de la API para comunicación con el Backend (Laravel)
api = FastAPI(title="RankPilot AI Core", version="1.0.0")
@api.get("/health")
async def health_check():
    """
    Verifica que el servidor FastAPI está corriendo correctamente.
    """
    return {
        "status": "online",
        "message": "Hola Mundo - RankPilot Core is alive",
        "version": "1.0.0",
        "environment": "Ubuntu/Docker"
    }

def run_rankpilot(user_input: str, thread_id: str, is_file: bool = False):
    config = {"configurable": {"thread_id": thread_id}}
    
    if is_file:
        print(f"--- [EJECUCIÓN: NUEVO CASO - ID: {thread_id}] ---")
        initial_state = {"file_path": user_input, "messages": []}
        output = graph_app.invoke(initial_state, config)
    else:
        print(f"--- [EJECUCIÓN: CONTINUACIÓN - ID: {thread_id}] ---")
        output = graph_app.invoke(
            {"messages": [HumanMessage(content=user_input)]}, 
            config
        )
    
    # --- LÓGICA ELEGANTE DE EXTRACCIÓN ---
    # Si el grafo terminó (is_complete), extraemos el path absoluto
    if output.get("is_complete"):
        raw_path = output.get("pdf_url")
        if raw_path:
            # Convertimos a path absoluto para que no haya dudas de dónde está
            absolute_path = os.path.abspath(raw_path)
            output["pdf_url"] = absolute_path
            print(f"✅ SUCCESS: PDF generated at {absolute_path}")
            
    return output

# 2. Endpoint General (Ajustado para devolver el path claramente)
@api.post("/process")
async def process_request(request: Request):
    data = await request.json()
    
    user_input = data.get("user_input")
    thread_id = data.get("thread_id", str(uuid.uuid4()))
    is_file = data.get("is_file", False)
    
    result = run_rankpilot(user_input, thread_id, is_file)
    
    # Devolvemos una respuesta estructurada
    return {
        "status": "success" if result.get("is_complete") else "pending",
        "thread_id": thread_id,
        "pdf_url": result.get("pdf_url"), # Aquí llegará el path absoluto
        "confidence_score": result.get("confidence_score"),
        "last_message": result["messages"][-1].content if result.get("messages") else None
    }

# 3. Bloque de prueba protegido (Ignorado por el servidor)
if __name__ == "__main__":
    print("--- MODO DE PRUEBA LOCAL ---")
    dummy_id = "test-session-001"
    dummy_text = "General firm information for system validation."
    
    # Prueba rápida de conectividad
    test_result = run_rankpilot(dummy_text, dummy_id, is_file=False)
    print("Test exitoso:", test_result is not None)