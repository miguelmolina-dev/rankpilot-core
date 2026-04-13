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
        gaps = []
        required_fields = self.config.get("required_fields", [])
        fields_config = self.config.get("fields", {})
        for field in required_fields:
            if field not in submission_data or not submission_data[field]:
                field_description = fields_config.get(field, {}).get("description", "")
                reason = f"Missing required field {field} for Legal500."
                if field_description:
                    reason += f" This section requires: {field_description}"
                gaps.append({"field": field, "reason": reason})
        return gaps

    def assemble(self, submission_data: Dict[str, Any], output_path: str) -> str:
        """
        Uses python-docx to assemble the Legal500 docx.
        """
        context = submission_data.copy()
        template_path = "templates/legal500-us-submissions-template-2026-1-1-2.docx"
        return assemble_submission(template_path, output_path, context)
