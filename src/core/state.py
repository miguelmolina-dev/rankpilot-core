import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from src.core.schemas import BaseSubmission


class AgentState(TypedDict):
    """
    Represents the state of our agent for LangGraph.
    """
    # Documents input as base64
    base64_documents: List[Dict[str, str]]

    # Paths to decoded input documents
    decoded_file_paths: List[str]

    # Type of submission (e.g. Legal500 US 2026, Chambers Global)
    submission_type: Optional[str]

    # The main structured data we are extracting and building
    submission: Optional[BaseSubmission]

    # Gap analysis results
    gaps: List[Dict[str, Any]]

    # Dynamic questions generated to cover gaps
    questions: List[str]

    # History of Q&A interactions with Laravel
    history: List[str]

    # Current question and incoming answer from Laravel
    new_answer: Dict[str, str]

    # Base64 output representation of the final document
    output_base64: Optional[str]

    # Optional fields for tracking process
    messages: Annotated[list, operator.add]
    current_step: str
    errors: List[str]
