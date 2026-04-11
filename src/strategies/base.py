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
