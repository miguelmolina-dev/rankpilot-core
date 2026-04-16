import operator
from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
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

    # The main structured data we are extracting and building
    submission: Optional[BaseSubmission] = None

    # Gap analysis results
    gaps: List[Dict[str, Any]] = Field(default_factory=list)

    # Dynamic questions generated to cover gaps
    questions: List[str] = Field(default_factory=list)

    # History of Q&A interactions with Laravel
    history: List[str] = Field(default_factory=list)

    # --- NEW: Accept raw text directly from the Laravel UI ---
    raw_input_text: str = ""

    # Current question and incoming answer from Laravel
    new_answer: Dict[str, str] = Field(default_factory=dict)

    # Base64 output representation of the final document
    output_base64: Optional[str] = None

    # Optional fields for tracking process
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    current_step: str = ""
    extracted_text: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    
    # --- NEW: Track fields the user explicitly skipped or doesn't have ---
    dismissed_gaps: List[str] = Field(default_factory=list)

    # ==========================================
    # NEW: The Sanitization Bouncer
    # ==========================================
    @field_validator("target_submission_type", mode="before")
    @classmethod
    def normalize_submission_type(cls, value: Optional[str]) -> Optional[str]:
        """
        Intercepts the incoming string from Laravel and aggressively cleans it.
        Converts 'Legal 500', 'Legal-500', 'legal_500' -> 'Legal500'
        """
        if not value:
            return value
            
        # 1. Convert to lowercase and strip out all spaces, hyphens, and underscores
        cleaned = value.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        # 2. Force it into the exact official formats
        if "legal" in cleaned and "500" in cleaned:
            return "Legal500"
        if "chambers" in cleaned:
            return "Chambers"
            
        # If it's something entirely different, return it capitalized just in case
        return value.capitalize()
