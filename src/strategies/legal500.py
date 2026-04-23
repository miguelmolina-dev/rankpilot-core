import yaml
from typing import Dict, Any, List
from src.strategies.base import SubmissionStrategy
from src.io.docx_manager import assemble_submission

class Legal500Strategy(SubmissionStrategy):
    """
    Submission strategy specifically for Legal500.
    Config-driven based on YAML definitions.
    """

    def __init__(self, config_path: str = "configs/legal500_us.yaml"):
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
        Soporta rutas de punto (dot-notation) para validar campos anidados.
        """
        required_fields = self.config.get("required_fields", [])
        gaps = []

        # Helper para navegar por rutas anidadas (ej. identity.firm_name)
        def get_nested_value(data, path):
            keys = path.split('.')
            curr = data
            try:
                for k in keys:
                    if isinstance(curr, dict):
                        curr = curr.get(k)
                    elif isinstance(curr, list) and k.isdigit():
                        curr = curr[int(k)]
                    else:
                        return None
                return curr
            except (KeyError, IndexError, TypeError):
                return None

        for field_path in required_fields:
            val = get_nested_value(submission_data, field_path)
            
            # Si el valor no existe o está vacío (None, "", [])
            if val in [None, "", []]:
                # Buscamos la descripción amigable en el YAML
                reason = self.config.get("fields", {}).get(field_path, {}).get("description")
                
                # Si no hay descripción específica, generamos una automática
                if not reason:
                    friendly_name = field_path.split('.')[-1].replace("_", " ").title()
                    reason = f"Please provide information for {friendly_name}."
                
                gaps.append({
                    "field": field_path, 
                    "reason": reason
                })
                
        return gaps

    def assemble(self, submission_data: Dict[str, Any], output_path: str) -> str:
        """
        Uses python-docx to assemble the Legal500 docx.
        """
        # 1. Start with the raw Pydantic dump
        context = submission_data.copy()

        # 2. FIX THE CAPITALIZATION & HIERARCHY
        context["Identity"] = context.get("identity", {})
        context["DepartmentInfo"] = context.get("department_info", {})
        context["Narratives"] = context.get("narratives", {})
        context["Metrics"] = context.get("DepartmentInfo", {}).get("metrics", {})

        # 3. FIX THE MATTERS LOOP (Blank tables & Python lists)
        pub_matters = context.get("publishable_matters", [])
        conf_matters = context.get("confidential_matters", [])
        for m in pub_matters + conf_matters:
            if isinstance(m.get("jurisdictions_involved"), list):
                m["jurisdictions_involved"] = ", ".join(m["jurisdictions_involved"])
            
            # Fix the Pydantic key mismatch so the template can find the partners
            m["leading_partners"] = m.get("lead_partners", [])
            m["other_partners"] = m.get("other_key_team_members", [])

            # Pad the lists so Word doesn't crash if there's only 1 partner listed
            while len(m["leading_partners"]) < 2:
                m["leading_partners"].append({"name": "", "office": "", "practice_area": ""})
            while len(m["other_partners"]) < 2:
                m["other_partners"].append({"name": "", "office": "", "practice_area": ""})
                
            if not m.get("external_firms_advising"):
                m["external_firms_advising"] = [{"firm_name": "", "role_details": "", "entity_advised": ""}]

        # 4. FIX THE WORK HIGHLIGHTS
        context["WorkHighlight"] = context.get("work_highlights_summaries", [])
        while len(context["WorkHighlight"]) < 3:
            context["WorkHighlight"].append({"publishable_summary": ""})

        # 5. CLEANUP: Strip trailing newlines from AI text to prevent bloated Word tables
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

        # 6. Build the document
        template_path = "templates/legal500-us-submissions-template-2026-1-1-2.docx"
        return assemble_submission(template_path, output_path, context)