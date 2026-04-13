from abc import ABC, abstractmethod
from typing import Dict, Any, List

class SubmissionStrategy(ABC):
    """
    Abstract Base Class for specific directory submission strategies (Legal500, Chambers).
    Follows Strategy Pattern for evaluating, auditing, and assembling submissions.
    """

    @abstractmethod
    def audit(self, submission_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Runs the Gap Analysis to compare the current JSON state against the
        'Ideal Schema' of the specific template (driven by config).
        Returns a list of identified gaps.
        """
        pass

    @abstractmethod
    def assemble(self, submission_data: Dict[str, Any], output_path: str) -> str:
        """
        Takes the complete JSON data and injects it into the respective .docx original template.
        Returns the path to the final assembled file.
        """
        pass

    def _evaluate_nested_fields(self, data: Dict[str, Any], required_fields: List[str], strategy_name: str) -> List[Dict[str, Any]]:
        """
        Helper method to evaluate dot-notation fields recursively and return detailed gaps.
        """
        gaps = []
        for field_path in required_fields:
            parts = field_path.split('.')
            current_value = data
            missing = False

            for part in parts:
                if isinstance(current_value, dict) and part in current_value:
                    current_value = current_value[part]
                else:
                    missing = True
                    break

            # A field is considered a gap if it's completely missing, or is None, an empty string, or an empty list.
            if missing or current_value is None or current_value == "" or current_value == []:
                gaps.append({
                    "field": field_path,
                    "reason": f"Missing required field {field_path} for {strategy_name}."
                })

        return gaps
