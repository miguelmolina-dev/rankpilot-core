import operator
from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.core.schemas import BaseSubmission


class AgentState(BaseModel):
    """
    Represents the state of our agent for LangGraph.
    """
    # Documents input as base64
    base64_documents: List[Dict[str, str]] = Field(default_factory=list)

    # Paths to decoded input documents
    decoded_file_paths: List[str] = Field(default_factory=list)

    # Type of submission (e.g. Legal500 US 2026, Chambers Global)
    target_submission_type: Optional[str] = None
    input_document_type: Optional[str] = None

    # The main structured data we are extracting and building
    submission: Optional[BaseSubmission] = None

    # Gap analysis results
    gaps: List[Dict[str, Any]] = Field(default_factory=list)

    # Dynamic questions generated to cover gaps
    questions: List[str] = Field(default_factory=list)

    # History of Q&A interactions with Laravel
    history: List[str] = Field(default_factory=list)

    # Current question and incoming answer from Laravel
    new_answer: Dict[str, str] = Field(default_factory=dict)

    # Base64 output representation of the final document
    output_base64: Optional[str] = None

    # Optional fields for tracking process
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    current_step: str = ""
    extracted_text: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
