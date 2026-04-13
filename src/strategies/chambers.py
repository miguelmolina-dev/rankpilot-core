import yaml
from typing import Dict, Any, List
from src.strategies.base import SubmissionStrategy

class ChambersStrategy(SubmissionStrategy):
    """
    Submission strategy specifically for Chambers.
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
        Runs the Gap Analysis to compare the current JSON state against the
        'Ideal Schema' of Chambers template.
        """
        required_fields = self.config.get("required_fields", [])
        return self._evaluate_nested_fields(submission_data, required_fields, "Chambers")

    def assemble(self, submission_data: Dict[str, Any], output_path: str) -> str:
        """
        Uses python-docx to assemble the Chambers docx.
        """
        # Mocking assembly
        return output_path
