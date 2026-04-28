import requests
import time
import uuid
import json
import base64  # <-- NUEVO: Para convertir el archivo
import os      # <-- NUEVO: Para verificar que el archivo existe

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
        print("\n[Simulador de Carga de Archivos]")
        # El .strip('"') es un truco por si arrastras el archivo a la consola en Windows
        ruta_archivo = input("📁 Arrastra o pega la ruta completa de tu archivo (.docx o .pdf): ").strip('"').strip("'")
        
        if os.path.exists(ruta_archivo):
            try:
                # 1. Leemos el archivo en modo binario
                with open(ruta_archivo, "rb") as archivo:
                    contenido_binario = archivo.read()
                
                # 2. Lo convertimos a Base64 y luego a un string de texto
                base64_string = base64.b64encode(contenido_binario).decode('utf-8')
                
                # 3. Extraemos solo el nombre del archivo (ej. "mi_caso.docx")
                nombre_archivo = os.path.basename(ruta_archivo)
                
                base64_docs = [{"filename": nombre_archivo, "base64": base64_string}]
                print(f"✅ Archivo '{nombre_archivo}' cargado y convertido a Base64 exitosamente!")
                
            except Exception as e:
                print(f"❌ Error al leer o convertir el archivo: {e}")
                return
        else:
            print(f"❌ Error: No se encontró ningún archivo en la ruta: {ruta_archivo}")
            return
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
        "target_submission_type": "Legal500",
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
            # Imprimimos qué endpoint estamos consultando
            print(f"\n[GET] {BASE_URL}/status/{current_job_id}")
            
            status_response = requests.get(f"{BASE_URL}/status/{current_job_id}")
            if status_response.status_code != 200:
                print("❌ Error en el polling:", status_response.text)
                return
                
            status_data = status_response.json()
            
            # ---> AQUÍ ESTÁ LA MAGIA: Imprimimos el JSON exacto de la respuesta
            print("📦 JSON recibido del servidor:")
            print(json.dumps(status_data, indent=2))
            
            if status_data["status"] == "started" or status_data["status"] == "processing":
                progreso = status_data.get('progress', 0)
                barra = "█" * (progreso // 5) + "-" * (20 - (progreso // 5))
                # Quitamos el \r para que el JSON no se borre de la consola
                print(f"[{barra}] {progreso}% - {status_data.get('message', '')}")
                time.sleep(2) # Esperar 2 segundos
                
            elif status_data["status"] == "completed":
                print(f"\n[{'█'*20}] 100% - ¡Proceso Completado!")
                break # Salimos del bucle de polling
            
            elif status_data["status"] == "failed":
                print("\n❌ EL TRABAJO FALLÓ EN EL SERVIDOR.")
                break
        
        if status_data["status"] == "failed":
            break
            
        # --- Evaluación del Resultado ---
        ia_data = status_data.get("data", {})
        if not ia_data:
            print("⚠️ Advertencia: No se encontró la llave 'data' en el JSON completado.")
            break
            
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
        
        # Extraemos la pregunta de forma segura
        preguntas = ia_data.get("questions", [])
        pregunta = preguntas[0] if preguntas else "¿Puedes proporcionar más detalles sobre esto?"
        print(f"🤖 IA: {pregunta}")
        
        # Pedimos respuesta al usuario por consola
        respuesta_usuario = input("\n👤 Tu respuesta: ")
        
        # Simulamos que el usuario le da clic a "Synthesize Answer"
        gap_actual = gaps[0]["field"] if gaps else "general"
        
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
        
        if resp.status_code != 200:
             print("❌ Error al enviar la respuesta:", resp.text)
             break
             
        # Recibimos el nuevo ticket y el ciclo grande se repite
        current_job_id = resp.json().get("job_id")
        print(f"✅ Nuevo Ticket recibido! Job ID: {current_job_id}")

if __name__ == "__main__":
    main()