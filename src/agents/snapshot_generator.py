from src.chains.snapshot_chain import snapshot_chain
from src.core.state import AgentState

def snapshot_generator_node(state: AgentState):
    print("--- [NODE] Generating Final Snapshot ---")
    
    try:
        submission_obj = getattr(state, "submission", None)
        submission_json = submission_obj.model_dump_json() if submission_obj else getattr(state, "raw_text", "")
        
        metadata = getattr(state, "metadata", None)
        practice_area = getattr(metadata, "practice_area", "Unknown") if metadata else "Unknown"
        history = getattr(state, "history", [])

        # --- NUEVO: Extraemos las reglas del YAML ---
        config = getattr(state, "config", {})
        guidelines = config.get("copywriting_guidelines", "Evaluate based on standard Band 1 metrics: complex matters, deep bench, and clear commercial impact.")

        result = snapshot_chain.invoke({
            "submission_json": submission_json,
            "history": "\n".join(history) if history else "No Q&A history.",
            "practice_area": practice_area,
            "editorial_rules": guidelines # <-- Inyectado
        })
        
        return {
            "positioning_core": {
                "practice_model": result.practice_model.label,
                "practice_definition": result.practice_model.definition,
                "confidence_score": result.confidence_score,
                "signals": result.signals
            },
            "positioning_tier": result.positioning_tier.model_dump(),
            "blind_spots": [bs.model_dump() for bs in result.blind_spots],
            "competitive_advantage": result.competitive_advantage,
            "errors": []
        }

    except Exception as e:
        print(f"!!! Error Crítico en Generación de Snapshot: {e}")
        import traceback
        traceback.print_exc()
        return {
            "errors": [f"Snapshot Error: {str(e)}"],
            "positioning_tier": {"label": "Error", "explanation": "System failure."}
        }