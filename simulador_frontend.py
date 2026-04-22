import requests
import time
import uuid
import json

# URL base donde corre nuestro simulador FastAPI
BASE_URL = "http://127.0.0.1:8000"

def print_header(texto):
    print(f"\n{'='*50}\n{texto}\n{'='*50}")

def main():
    print_header("🚀 RANKPILOT FRONTEND SIMULATOR (CLI)")
    print("Selecciona tu vía de entrada:")
    print("1. 📄 Upload Draft (.docx)")
    print("2. ✍️ Paste Raw Text")
    print("3. ✨ Start from Scratch")
    
    opcion = input("\nElige una opción (1/2/3): ")
    
    input_type = "scratch"
    base64_docs = []
    raw_text = ""
    
    if opcion == "1":
        input_type = "docx"
        base64_docs = [{"filename": "documento_falso.docx", "base64": "JVBERi0xLj..."}]
        print("\n[Simulando archivo .docx convertido a Base64...]")
    elif opcion == "2":
        input_type = "raw_text"
        raw_text = input("\nPega tu texto crudo aquí: ")
    elif opcion == "3":
        input_type = "scratch"
        print("\n[Iniciando lienzo en blanco...]")
    else:
        print("Opción no válida. Saliendo...")
        return

    # 1. ESTADO INICIAL (Generado en el "Frontend")
    thread_id = str(uuid.uuid4())
    agent_state = {
        "metadata": {
            "directory": "Legal500",
            "guide": "Latin America",
            "practice_area": "Fintech"
        },
        "input_document_type": input_type,
        "base64_documents": base64_docs,
        "raw_input_text": raw_text,
        "submission": {},
        "gaps": []
    }

    # 2. ENVIAR PETICIÓN INICIAL
    print("\n📡 Enviando POST a /api/process...")
    payload = {
        "thread_id": thread_id,
        "agent_state": agent_state
    }
    
    response = requests.post(f"{BASE_URL}/process", json=payload)
    if response.status_code != 200:
        print("❌ Error del servidor:", response.text)
        return
        
    job_data = response.json()
    current_job_id = job_data["job_id"]
    print(f"✅ Ticket recibido! Job ID: {current_job_id}")
    
    # 3. CICLO INFINITO DE LA APLICACIÓN
    while True:
        print("\n⏳ Iniciando Polling (consultando cada 2s)...")
        
        # --- Bucle de Polling ---
        while True:
            status_response = requests.get(f"{BASE_URL}/status/{current_job_id}")
            if status_response.status_code != 200:
                print("❌ Error en el polling:", status_response.text)
                return
                
            status_data = status_response.json()
            
            if status_data["status"] == "processing":
                # Dibujamos una barra de progreso rudimentaria en la consola
                progreso = status_data['progress']
                barra = "█" * (progreso // 5) + "-" * (20 - (progreso // 5))
                print(f"\r[{barra}] {progreso}% - {status_data['message']}", end="", flush=True)
                time.sleep(2) # Esperar 2 segundos
                
            elif status_data["status"] == "completed":
                print(f"\r[{'█'*20}] 100% - ¡Proceso Completado!        ")
                break # Salimos del bucle de polling
        
        # --- Evaluación del Resultado ---
        ia_data = status_data.get("data", {})
        gaps = ia_data.get("gaps", [])
        
        # Actualizamos nuestro agent_state con lo que nos devolvió la IA
        agent_state["submission"] = ia_data.get("submission", {})
        agent_state["gaps"] = gaps
        
        # CONDICIÓN DE SALIDA: Si no hay gaps, terminamos.
        if not gaps:
            print_header("🏆 DIAGNÓSTICO ESTRATÉGICO FINAL (Acto 3)")
            print("¡La IA determinó que no hay más brechas de información!")
            print("Mostrando Dashboard Final con la puntuación y el botón de descarga...")
            break
            
        # SI HAY GAPS: Iniciamos el chat
        print_header(f"🛑 AUDIT ROOM: {len(gaps)} errores encontrados")
        
        # Mostramos la pregunta de la IA
        pregunta = ia_data["questions"][0]
        print(f"🤖 IA: {pregunta}")
        
        # Pedimos respuesta al usuario por consola
        respuesta_usuario = input("\n👤 Tu respuesta: ")
        
        # Simulamos que el usuario le da clic a "Synthesize Answer"
        # Preparamos el nuevo JSON para enviar
        gap_actual = gaps[0]["field"]
        
        agent_state["new_answer"] = {
            "target_field": gap_actual,
            "question_text": pregunta,
            "answer": respuesta_usuario
        }
        
        payload_respuesta = {
            "thread_id": thread_id,
            "agent_state": agent_state
        }
        
        print("\n📡 Enviando respuesta POST a /api/process...")
        resp = requests.post(f"{BASE_URL}/process", json=payload_respuesta)
        
        # Recibimos el nuevo ticket y el ciclo grande se repite
        current_job_id = resp.json()["job_id"]
        print(f"✅ Nuevo Ticket recibido! Job ID: {current_job_id}")

if __name__ == "__main__":
    # Necesitas tener instalada la librería requests: pip install requests
    main()