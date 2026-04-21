import yaml
from typing import Dict, Any, List
from src.strategies.base import SubmissionStrategy
from src.io.docx_manager import assemble_submission

class LeadersLeagueStrategy(SubmissionStrategy):
    """
    Submission strategy specifically for Leaders League templates.
    Config-driven based on YAML definitions.
    """

    def __init__(self, config_path: str = "configs/leaders_league_advertising.yaml"):
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
        Upgraded to parse dictionaries containing 'field' and 'description' 
        from the new YAML architecture.
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

        for item in required_fields:
            # EXTRACT FROM THE DICTIONARY:
            field_path = item.get("field")
            # If a description exists, pass it along as the reason!
            description = item.get("description", f"Please provide information for {field_path}.")

            val = get_nested_value(submission_data, field_path)
            
            # If the field doesn't exist, is an empty string, or an empty list
            if val in [None, "", []]:
                gaps.append({
                    "field": field_path, 
                    "reason": description # <--- The AI will read this exact description!
                })
                
        return gaps

    def assemble(self, submission_data: Dict[str, Any], output_path: str) -> str:
        """
        Uses python-docx to prepare data and assemble the Leaders League docx.
        Pads all arrays to prevent IndexError in docxtpl.
        """
        # ==========================================
        # 1. TRANSLATION DICTIONARY (Pydantic -> Jinja2)
        # ==========================================
        context = {
            "firm_information": submission_data.get("firm_information", {}),
            "department_information": submission_data.get("department_information", {}),
            "peer_feedback": submission_data.get("peer_feedback", {}),
            "ranking_feedback": submission_data.get("ranking_feedback", {}),
            "work_highlights": submission_data.get("work_highlights", [])
        }

        # Ensure all base sections exist as dictionaries/lists to prevent KeyErrors
        for key in ["firm_information", "department_information", "peer_feedback", "ranking_feedback"]:
            if not context[key]:
                context[key] = {}
        if not context["work_highlights"]:
            context["work_highlights"] = []

        # ---------------------------------------------------------
        # 2. THE PADDING ENGINE (Prevents docxtpl IndexErrors)
        # ---------------------------------------------------------
        def pad_array(parent_dict, key, required_length, fill_type=dict):
            arr = parent_dict.setdefault(key, [])
            while len(arr) < required_length:
                arr.append(fill_type())
            return arr

        # Pad Department Info
        dep_info = context["department_information"]
        pad_array(dep_info, "department_heads", 5)
        pad_array(dep_info, "department_changes", 5)
        pad_array(dep_info, "top_five_sectors", 5, fill_type=str) # Pad with empty strings
        pad_array(dep_info, "active_clients", 30)                 # Pad to 30 clients

        # Pad Peer Feedback
        peer_info = context["peer_feedback"]
        pad_array(peer_info, "established_practitioners", 5)
        pad_array(peer_info, "rising_stars", 5)

        # Pad Work Highlights (Top-level list)
        wh = context["work_highlights"]
        while len(wh) < 10:
            wh.append({})

        # ---------------------------------------------------------
        # 3. BOOLEAN FIXES FOR Y/N
        # ---------------------------------------------------------
        # Translate Client booleans
        for client in dep_info.get("active_clients", []):
            for key in ["is_new_client", "is_confidential"]:
                val = client.get(key)
                if val in [True, "True", "true", "Y", "Yes"]:
                    client[key] = "Y"
                elif val in [False, "False", "false", "N", "No"]:
                    client[key] = "N"

        # Translate Work Highlight booleans
        for highlight in context.get("work_highlights", []):
            val = highlight.get("is_confidential")
            if val in [True, "True", "true", "Y", "Yes"]:
                highlight["is_confidential"] = "Y"
            elif val in [False, "False", "false", "N", "No"]:
                highlight["is_confidential"] = "N"

        # ---------------------------------------------------------
        # 4. CLEANUP: Strip trailing newlines
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

        # 5. BUILD THE DOCUMENT
        template_name = "advertising-and-marketing-2026_696fc8957cfef.docx"
        template_path = f"templates/{template_name}"
        
        return assemble_submission(template_path, output_path, context)