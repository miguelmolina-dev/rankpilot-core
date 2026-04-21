from typing import Dict, Any
import json
from src.core.state import AgentState
from src.chains.executive_writer_chain import executive_writer_chain
import datetime

def executive_writer_node(state: AgentState) -> Dict[str, Any]:
    """
    Executive Writer Agent:
    Synthesizes all technical and strategic data into a high-authority 
    report and a formal Audit Letter.
    """
    print("--- [NODE] Finalizing Executive Synthesis ---")

    # 1. Extraer metadata y asegurar el nombre de la firma
    metadata = getattr(state, "metadata", {})
    submission_obj = getattr(state, "submission", None)
    
    # Intenta sacar el nombre de metadata, si no, del submission, si no, genérico.
    firm_name = "the Firm"
    if metadata and getattr(metadata, "firm_name", ""):
        firm_name = getattr(metadata, "firm_name")
    elif submission_obj and hasattr(submission_obj, "identity") and submission_obj.identity.firm_name:
        firm_name = submission_obj.identity.firm_name

    # 2. Formatear las entradas complejas a texto legible para el LLM
    pos_core = getattr(state, "positioning_core", {})
    pos_tier = getattr(state, "positioning_tier", {})
    comp_adv = getattr(state, "competitive_advantage", [])
    blind_spots = getattr(state, "blind_spots", [])
    evolution_path = getattr(state, "evolution_path", [])

    formatted_path = "\n".join([
        f"STEP {i+1}: {getattr(step, 'action_title', step.get('action_title', '')) if isinstance(step, dict) else getattr(step, 'action_title', '')} ({getattr(step, 'category', step.get('category', '')) if isinstance(step, dict) else getattr(step, 'category', '')})\n"
        f"WHY: {getattr(step, 'why_it_matters', step.get('why_it_matters', '')) if isinstance(step, dict) else getattr(step, 'why_it_matters', '')}\n"
        f"HOW: {getattr(step, 'technical_instruction', step.get('technical_instruction', '')) if isinstance(step, dict) else getattr(step, 'technical_instruction', '')}\n"
        # --- CAMBIO: Usamos target_completion_date ---
        f"TIMELINE: Must be completed by {getattr(step, 'target_completion_date', step.get('target_completion_date', 'N/A')) if isinstance(step, dict) else getattr(step, 'target_completion_date', 'N/A')}.\n"
        for i, step in enumerate(evolution_path)
    ]) if evolution_path else "No roadmap generated."

    formatted_blind_spots = "\n".join([
        f"- {bs.get('issue', '') if isinstance(bs, dict) else getattr(bs, 'issue', '')}" 
        for bs in blind_spots
    ]) if blind_spots else "None identified."

    current_date = datetime.date.today().strftime("%B %d, %Y")

    # 3. Preparar el Payload
    input_data = {
        "current_date": current_date,
        "firm_name": firm_name,
        "practice_area": getattr(metadata, "practice_area", "General Law") if isinstance(metadata, dict) else "General Law",
        "region": getattr(metadata, "region", "Global") if isinstance(metadata, dict) else "Global",
        "positioning_tier": json.dumps(pos_tier) if isinstance(pos_tier, dict) else str(pos_tier),
        "competitive_advantage": ", ".join(comp_adv) if comp_adv else "General Practice",
        "gaps": "0 Structural Gaps (Fully optimized submission)", # En el Acto 3, los gaps físicos ya son cero
        "blind_spots": formatted_blind_spots,
        "evolution_path": formatted_path,
        "positioning_core": json.dumps(pos_core) if isinstance(pos_core, dict) else str(pos_core),
        "history": "\n".join(getattr(state, "history", []))
    }
    
    try:
        print("--- [DEBUG] Calling Executive Writer LLM ---")
        response = executive_writer_chain.invoke(input_data)
        
        print(f"--- [DEBUG] Synthesis Complete. Overall Score: {response.overall_score} ---")

        # 4. Final State Update
        return {
            "executive_summary": {
                "overall_score": response.overall_score,
                "risk_level": response.risk_level,
                "strategic_verdict": response.strategic_verdict,
                "top_differentiators": comp_adv,
                "audit_letter_markdown": response.audit_letter_markdown
            },
            "current_step": "completed" # <-- FIX: Evita el TypeError de concatenación
        }
    except Exception as e:
        print(f"--- [ERROR] Executive Writer Node Failed: {str(e)} ---")
        import traceback
        traceback.print_exc()
        return {
            "executive_summary": {
                "overall_score": 0,
                "risk_level": "Critical",
                "strategic_verdict": "Synthesis Failed. No actionable insights generated.",
                "top_differentiators": [],
                "audit_letter_markdown": "An error occurred during synthesis. Please review the logs."
            },
            "current_step": "completed_with_errors"
        }