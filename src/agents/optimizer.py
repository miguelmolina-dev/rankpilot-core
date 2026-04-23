from typing import Dict, Any
import json
from src.core.state import AgentState
from src.chains.optimizer_chain import narrative_chain, matter_chain, summary_chain

def optimize_node(state: AgentState) -> Dict[str, Any]:
    print("--- [NODE] Executing Submission Optimizer (Ghostwriter) ---")
    
    updates = {"messages": []}
    submission_obj = getattr(state, "submission", None)
    
    if not submission_obj:
        updates["messages"].append("Optimizer skipped: No submission data found.")
        return updates

    config = getattr(state, "config", {})
    guidelines = config.get("copywriting_guidelines", "Follow standard professional legal writing standards.")
    
    # Pasamos el objeto a diccionario para poder modificarlo
    sub_dict = submission_obj.model_dump()

    # ========================================================
    # 1. OPTIMIZAR NARRATIVAS (Visión de la Firma)
    # ========================================================
    print("--- [DEBUG] Optimizing Narratives ---")
    try:
        narrative_context = {
            "narratives": sub_dict.get("narratives", {})
        }
        
        nar_resp = narrative_chain.invoke({
            "narrative_json": json.dumps(narrative_context),
            "copywriting_guidelines": guidelines
        })
        
        if "narratives" in sub_dict and sub_dict["narratives"]:
            if nar_resp.what_sets_us_apart:
                sub_dict["narratives"]["what_sets_us_apart"] = nar_resp.what_sets_us_apart
            if nar_resp.initiatives_and_innovation:
                sub_dict["narratives"]["initiatives_and_innovation"] = nar_resp.initiatives_and_innovation
    except Exception as e:
        print(f"!!! Narrative Optimization Failed: {e}")

    # ========================================================
    # 2. OPTIMIZAR WORK HIGHLIGHTS SUMMARIES (Legal 500)
    # ========================================================
    print("--- [DEBUG] Optimizing Work Highlights Summaries ---")
    summaries = sub_dict.get("work_highlights_summaries", [])
    for i, summary in enumerate(summaries):
        try:
            raw_text = summary.get("publishable_summary", "")
            if raw_text and len(raw_text.split()) > 30: # Solo condensamos si es muy largo
                print(f"  -> Condensing Summary {i+1} / {len(summaries)} down to 40 words...")
                s_resp = summary_chain.invoke({
                    "raw_summary": raw_text
                })
                # Reemplazamos el texto largo por la versión condensada
                summary["publishable_summary"] = s_resp.short_summary
            else:
                print(f"  -> Summary {i+1} is already short. Skipping.")
        except Exception as e:
            print(f"  -> Error condensing Summary {i+1}: {e}")

    # ========================================================
    # 3. OPTIMIZAR CASOS PUBLICABLES (El Especialista)
    # ========================================================
    print("--- [DEBUG] Optimizing Publishable Matters ---")
    publishable = sub_dict.get("publishable_matters", [])
    for i, matter in enumerate(publishable):
        try:
            print(f"  -> Rewriting Publishable Matter {i+1} / {len(publishable)}...")
            m_resp = matter_chain.invoke({
                "matter_json": json.dumps(matter),
                "copywriting_guidelines": guidelines,
                "confidential_status": "FALSE (Publishable)"
            })
            matter["matter_description"] = m_resp.optimized_description
        except Exception as e:
            print(f"  -> Error rewriting Matter {i+1}: {e}")

    # ========================================================
    # 3. OPTIMIZAR CASOS CONFIDENCIALES
    # ========================================================
    print("--- [DEBUG] Optimizing Confidential Matters ---")
    confidential = sub_dict.get("confidential_matters", [])
    for i, matter in enumerate(confidential):
        try:
            print(f"  -> Rewriting Confidential Matter {i+1} / {len(confidential)}...")
            m_resp = matter_chain.invoke({
                "matter_json": json.dumps(matter),
                "copywriting_guidelines": guidelines,
                "confidential_status": "TRUE (Strictly Confidential - Focus on mechanics, protect identities)"
            })
            matter["matter_description"] = m_resp.optimized_description
        except Exception as e:
            print(f"  -> Error rewriting Matter {i+1}: {e}")

    # Empaquetamos de vuelta a Pydantic
    updates["submission"] = type(submission_obj)(**sub_dict)
    updates["messages"].append(f"SUCCESS: Optimized Narratives and {len(publishable) + len(confidential)} Matters.")
    print("--- [SUCCESS] Ghostwriter complete ---")

    return updates