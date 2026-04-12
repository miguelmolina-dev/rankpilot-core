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
        Runs the Gap Analysis to compare the current JSON state against the
        'Ideal Schema' of Legal500 template.
        """
        # A simple placeholder logic using the config
        # In a real scenario, this would compare data against required fields defined in self.config
        gaps = []
        required_fields = self.config.get("required_fields", [])
        for field in required_fields:
            if field not in submission_data or not submission_data[field]:
                gaps.append({"field": field, "reason": f"Missing required field {field} for Legal500."})
        return gaps

    def assemble(self, submission_data: Dict[str, Any], output_path: str) -> str:
        """
        Uses python-docx to assemble the Legal500 docx.
        """
        context = submission_data.copy()

        if "identity" in context and context["identity"]:
            context["Identity"] = context["identity"]
            contacts = context["identity"].get("interview_contacts", [])
            if contacts:
                context["InterviewContact"] = contacts[0]

        if "department_info" in context and context["department_info"]:
            context["DepartmentInfo"] = context["department_info"]
            heads = context["department_info"].get("heads_of_team", [])
            if heads:
                context["HeadOfTeam"] = heads[0]
            context["Metrics"] = context["department_info"].get("metrics", {})

        if "narratives" in context and context["narratives"]:
            context["Narratives"] = context["narratives"]

        if "team_dynamics" in context and context["team_dynamics"]:
            context["ArrivalDeparture"] = context["team_dynamics"].get("arrivals_and_departures", [])

        if "work_highlights_summaries" in context:
            context["WorkHighlight"] = context["work_highlights_summaries"]

        template_path = "templates/legal500-us-submissions-template-2026-1-1-2.docx"
        return assemble_submission(template_path, output_path, context)
