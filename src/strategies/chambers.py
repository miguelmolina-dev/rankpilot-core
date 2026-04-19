import yaml
from typing import Dict, Any, List
from src.strategies.base import SubmissionStrategy
from src.io.docx_manager import assemble_submission

class ChambersStrategy(SubmissionStrategy):
    """
    Submission strategy specifically for Chambers (Global and USA).
    Config-driven based on YAML definitions.
    """

    def __init__(self, config_path: str = "configs/chambers.yaml"):
        self.config_path = config_path
        self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.config = {}

    def audit(self, submission_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Runs the Gap Analysis.
        CRITICAL: Outputs the FULL dot-notation path so the Answer Evaluator knows exactly where to inject the data.
        """
        required_fields = self.config.get("required_fields", [])
        gaps = []

        # Helper to safely check if a deeply nested path exists and has data
        def get_nested_value(data, path):
            keys = path.split('.')
            curr = data
            try:
                for k in keys:
                    if k.isdigit():
                        curr = curr[int(k)]
                    else:
                        curr = curr[k]
                return curr
            except (KeyError, IndexError, TypeError):
                return None

        for field_path in required_fields:
            val = get_nested_value(submission_data, field_path)
            # If the field doesn't exist, is an empty string, or an empty list
            if val in [None, "", []]:
                # We KEEP the full dot-notation path!
                friendly_name = field_path.split('.')[-1].replace("_", " ").title()
                gaps.append({
                    "field": field_path, 
                    "reason": f"Please provide information for {friendly_name}."
                })
                
        return gaps

    def assemble(self, submission_data: Dict[str, Any], output_path: str) -> str:
        """
        Uses python-docx to prepare data and assemble the Chambers docx.
        Pads all arrays to prevent IndexError in docxtpl.
        """
        # ==========================================
        # 1. TRANSLATION DICTIONARY (Pydantic -> Jinja2)
        # ==========================================
        context = {
            "SectionA": submission_data.get("A_preliminary_information", {}),
            "SectionB": submission_data.get("B_department_information", {}),
            "SectionC": submission_data.get("C_feedback", {}),
            "D_publishable_information": submission_data.get("D_publishable_information", {}),
            "E_confidential_information": submission_data.get("E_confidential_information", {}),
            "target_submission_type": submission_data.get("target_submission_type", "Chambers_Global")
        }

        # Ensure all base sections exist to prevent KeyErrors (Safe fallback)
        context.setdefault("SectionA", {})
        context.setdefault("SectionB", {})
        context.setdefault("SectionC", {})
        context.setdefault("D_publishable_information", {})
        context.setdefault("E_confidential_information", {})

        # FLAG FOR USA vs GLOBAL LOGIC:
        target_type = context.get("target_submission_type", "Chambers_Global")
        context["is_global_template"] = target_type == "Chambers_Global"

        # ---------------------------------------------------------
        # 1. THE PADDING ENGINE (Prevents docxtpl IndexErrors)
        # ---------------------------------------------------------
        def pad_array(parent_dict, key, required_length):
            arr = parent_dict.setdefault(key, [])
            while len(arr) < required_length:
                arr.append({})
            return arr

        # Pad Preliminary Info
        pad_array(context["SectionA"], "A4_contact_persons", 2)
        
        # Pad Department Info
        pad_array(context["SectionB"], "B4_department_heads", 2)
        pad_array(context["SectionB"], "B8_hires_departures_last_12_months", 3)
        pad_array(context["SectionB"], "B9_lawyers_ranked_unranked", 6)

        # Pad Feedback
        pad_array(context["SectionC"], "C1_barristers_advocates", 8)

        # Pad Clients & Matters
        pad_array(context["D_publishable_information"], "D0_publishable_clients_list", 10)
        pad_array(context["D_publishable_information"], "publishable_matters", 10)
        
        pad_array(context["E_confidential_information"], "E0_confidential_clients_list", 10)
        pad_array(context["E_confidential_information"], "confidential_matters", 10)

        # ---------------------------------------------------------
        # 2. BOOLEAN FIXES FOR Y/N
        # ---------------------------------------------------------
        lawyers = context["SectionB"]["B9_lawyers_ranked_unranked"]
        for lawyer in lawyers:
            for key in ["is_partner", "is_ranked"]:
                val = lawyer.get(key)
                if val in [True, "True", "true", "Y", "Yes"]:
                    lawyer[key] = "Y"
                elif val in [False, "False", "false", "N", "No"]:
                    lawyer[key] = "N"
                else:
                    lawyer[key] = ""

        # ---------------------------------------------------------
        # 3. CLEANUP: Strip trailing newlines
        # ---------------------------------------------------------
        def clean_strings(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, str):
                        d[k] = v.strip()
                    elif isinstance(v, (dict, list)):
                        clean_strings(v)
            elif isinstance(d, list):
                for i in range(len(d)):
                    if isinstance(d[i], str):
                        d[i] = d[i].strip()
                    elif isinstance(d[i], (dict, list)):
                        clean_strings(d[i])
                        
        clean_strings(context)

        # 4. BUILD THE DOCUMENT
        template_name = "USA_Chambers_submission_form_template.docx" if context["is_global_template"] else "USA_Chambers_submission_form_template.docx"
        template_path = f"templates/{template_name}"
        
        return assemble_submission(template_path, output_path, context)