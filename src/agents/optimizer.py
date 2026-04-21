from typing import Dict, Any
import json
from src.core.state import AgentState
from src.chains.optimizer_chain import optimizer_chain

def optimize_node(state: AgentState) -> Dict[str, Any]:
    print("--- [NODE] Executing Submission Optimizer (Ghostwriter) ---")
    
    updates = {"messages": []}
    submission_obj = getattr(state, "submission", None)
    
    if not submission_obj:
        updates["messages"].append("Optimizer skipped: No submission data found.")
        return updates

    submission_json = submission_obj.model_dump_json()
    
    # --- NUEVO: Extraemos las reglas del YAML ---
    config = getattr(state, "config", {})
    guidelines = config.get("copywriting_guidelines", "Follow standard professional, objective, and factual legal writing standards. Avoid marketing fluff.")

    try:
        print("--- [DEBUG] Calling Optimizer LLM ---")
        response = optimizer_chain.invoke({
            "submission_json": submission_json,
            "copywriting_guidelines": guidelines # <-- Inyectado
        })
        
        sub_dict = submission_obj.model_dump()
        
        if "B_department_information" in sub_dict and sub_dict["B_department_information"]:
            sub_dict["B_department_information"]["B10_department_best_known_for"] = response.narratives.best_known_for
        elif "narratives" in sub_dict and sub_dict["narratives"]:
            sub_dict["narratives"]["what_sets_us_apart"] = response.narratives.best_known_for

        if "D_publishable_information" in sub_dict and sub_dict["D_publishable_information"]:
            matters = sub_dict["D_publishable_information"].get("publishable_matters", [])
            for i, matter in enumerate(matters):
                opt_matter = next((m for m in response.matters if m.matter_id == i), None)
                if opt_matter:
                    matter["D2_summary_of_matter_and_role"] = opt_matter.optimized_description

        if "matters" in sub_dict:
            for i, matter in enumerate(sub_dict["matters"]):
                opt_matter = next((m for m in response.matters if m.matter_id == i), None)
                if opt_matter:
                    matter["matter_description"] = opt_matter.optimized_description

        updates["submission"] = type(submission_obj)(**sub_dict)
        updates["messages"].append("SUCCESS: Submission narratives and matters strategically optimized based on Directory Rules.")

    except Exception as e:
        print(f"!!! Optimizer Failure: {e}")
        updates["messages"].append(f"WARNING: Optimization failed. Error: {e}")

    return updates