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

    # --- RAW TEXT INPUT ---
    raw_input_text: str = ""

    # --- FIX: Flexibilidad total para Laravel ---
    # Cambiamos Dict[str, str] por Dict[str, Any] para atrapar nulls antes de que explote
    new_answer: Dict[str, Any] = Field(default_factory=dict)

    # Base64 output representation of the final document
    output_base64: Optional[str] = None

    # Optional fields for tracking process
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    current_step: str = ""
    extracted_text: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    
    # Track fields the user explicitly skipped
    dismissed_gaps: List[str] = Field(default_factory=list)

    # ==========================================
    # VALIDADOR: NORMALIZAR TIPO DE SUBMISSION
    # ==========================================
    @field_validator("target_submission_type", mode="before")
    @classmethod
    def normalize_submission_type(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        cleaned = value.lower().replace(" ", "").replace("-", "").replace("_", "")
        if "legal" in cleaned and "500" in cleaned:
            return "Legal500"
        if "chambers" in cleaned:
            return "Chambers"
        return value.capitalize()
    
    # ==========================================
    # VALIDADOR: ESCUDO ANTI-PHP PARA SUBMISSION
    # ==========================================
    @field_validator("submission", mode="before")
    @classmethod
    def sanitize_php_garbage(cls, v: Optional[Any]) -> Optional[Any]:
        if isinstance(v, dict):
            buggy_fields = ["narratives", "individual_nominations", "team_dynamics"]
            for field in buggy_fields:
                if field in v and isinstance(v[field], dict) and "stdClass" in v[field]:
                    v[field] = {}
        return v

    # ==========================================
    # NEW: ESCUDO PARA NEW_ANSWER (The Null Killer)
    # ==========================================
    @field_validator("new_answer", mode="before")
    @classmethod
    def sanitize_new_answer(cls, v: Any) -> Dict[str, str]:
        """
        Si Laravel manda null en target_field, question_text o answer,
        lo convertimos en "" para que Pydantic no llore.
        """
        default = {"target_field": "", "question_text": "", "answer": ""}
        
        if not isinstance(v, dict):
            return default
            
        return {
            "target_field": str(v.get("target_field") or ""),
            "question_text": str(v.get("question_text") or ""),
            "answer": str(v.get("answer") or "")
        }
