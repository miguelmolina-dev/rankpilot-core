from typing import Dict, Any
from src.core.state import AgentState # <-- Actualizado al estado unificado
from src.chains.scheduler_chain import scheduler_chain
import datetime

def scheduler_node(state: AgentState) -> Dict[str, Any]:
    print("--- [NODE] Executing Strategic Scheduler ---")

    metadata = getattr(state, "metadata", None)
    
    # Extraer metadata de forma segura
    submission_deadline = getattr(metadata, "submission_deadline", "No deadline provided") if metadata else "No deadline provided"
    location = getattr(metadata, "location", "Global") if metadata else "Global"
    practice_area = getattr(metadata, "practice_area", "General Law") if metadata else "General Law"
    
    # Blind spots generados por el snapshot_generator
    raw_blind_spots = getattr(state, "blind_spots", [])
    formatted_blind_spots = ""
    for bs in raw_blind_spots:
        issue = getattr(bs, 'issue', bs.get('issue', 'Unknown Issue') if isinstance(bs, dict) else 'Unknown Issue')
        desc = getattr(bs, 'description', bs.get('description', '') if isinstance(bs, dict) else '')
        formatted_blind_spots += f"- {issue}: {desc}\n"

    # Los gaps del Acto 1 (En este punto deberían ser 0, pero por si acaso hay residuales)
    raw_gaps = getattr(state, "gaps", [])
    formatted_gaps = ""
    if isinstance(raw_gaps, list) and len(raw_gaps) > 0:
        if isinstance(raw_gaps[0], dict):
            formatted_gaps = "\n".join([f"- {g.get('field', 'Field')}: {g.get('reason', '')}" for g in raw_gaps])
        else:
            formatted_gaps = "\n".join([f"- {g}" for g in raw_gaps])
    else:
        formatted_gaps = "No structural gaps remaining. Focus entirely on narrative depth."

    # Usamos el JSON del submission ya optimizado como evidencia base
    submission_obj = getattr(state, "submission", None)
    raw_text = submission_obj.model_dump_json() if submission_obj else getattr(state, "raw_text", "")
    submission_json = getattr(state, "submission", None).model_dump_json() if getattr(state, "submission", None) else "{}"
    current_date = datetime.date.today().strftime("%B %d, %Y") # Ej: October 26, 2023
    input_data = {
        "current_date": current_date,
        "submission_deadline": submission_deadline,
        "location": location,
        "practice_area": practice_area,
        "gaps": formatted_gaps,
        "blind_spots": formatted_blind_spots,
        "submission_json": submission_json,
    }

    try:
        print(f"--- [DEBUG] Calling Scheduler LLM ---")
        response = scheduler_chain.invoke(input_data)
        
        return {
            "evolution_path": [m.model_dump() for m in response.evolution_path],
            # Manejamos el current_step tanto si es int como str
            "current_step": "scheduler_complete" 
        }
    except Exception as e:
        print(f"!!! Scheduler Parser Failure: {e}")
        import traceback
        traceback.print_exc()
        return {"evolution_path": [], "errors": [f"Scheduler Error: {e}"]}