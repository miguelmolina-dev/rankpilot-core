import operator
from typing import Annotated, List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from src.core.schemas import BaseSubmission

# ==========================================
# 1. MODELOS DE RANKPILOT (Positioning & Strategy)
# ==========================================
class PositioningCore(BaseModel):
    practice_model: str = ""
    practice_definition: str = ""
    confidence_score: float = 0.0
    signals: List[str] = Field(default_factory=list)

class PositioningTier(BaseModel):
    label: str = ""
    explanation: str = ""

class BlindSpot(BaseModel):
    issue: str = ""
    description: str = ""

class Milestone(BaseModel):
    category: str
    action_title: str
    why_it_matters: str
    technical_instruction: str
    priority_level: int
    target_completion_date: str

class ExecutiveSummary(BaseModel):
    overall_score: int = 0
    risk_level: str = ""
    strategic_verdict: str = ""
    top_differentiators: List[str] = Field(default_factory=list)
    audit_letter_markdown: str = ""

class MetaData(BaseModel):
    file_base64: str = ""
    target_band: Optional[str] = None
    directory: Optional[str] = None
    guide: str = Field(default="", description="Guide/Book/Research Edition")
    region: str = Field(default="", description="Región")
    practice_area: str = ""
    jurisdiction: str = Field(default="", description="Jurisdicción")
    location: str = ""
    submission_deadline: str = Field(
        default="", 
        description="The official deadline for this submission. Used by the Scheduler to calculate urgency."
    )
    firm_name: str = ""


# ==========================================
# 2. EL SÚPER ESTADO UNIFICADO
# ==========================================
class AgentState(BaseModel):
    """
    El 'Súper Estado' que fusiona el constructor de Submissions y el RankPilot Engine.
    """
    # --- Identificación y Metadata ---
    submission_id: str = ""
    target_submission_type: Optional[str] = None
    input_document_type: Optional[str] = None
    metadata: Optional[MetaData] = None
    
    # --- Archivos y Texto Extraído ---
    base64_documents: List[Dict[str, str]] = Field(default_factory=list)
    decoded_file_paths: List[str] = Field(default_factory=list)
    raw_text: str = "" # Usado por RankPilot para el análisis
    extracted_text: Optional[str] = None # Legacy de Submissions
    output_base64: Optional[str] = None
    
    # --- El Corazón de Submissions ---
    submission: Optional[BaseSubmission] = None
    gaps: List[Dict[str, Any]] = Field(default_factory=list) # Formato dict para dot-notation
    dismissed_gaps: List[str] = Field(default_factory=list)
    new_answer: Dict[str, Any] = Field(default_factory=dict) # Protegido por el Null Killer
    questions: List[str] = Field(default_factory=list)
    
    # --- El Corazón de RankPilot ---
    positioning_core: Optional[PositioningCore] = None
    positioning_tier: Optional[PositioningTier] = None
    blind_spots: List[BlindSpot] = Field(default_factory=list)
    competitive_advantage: List[str] = Field(default_factory=list)
    evolution_path: List[Milestone] = Field(default_factory=list)
    executive_summary: Optional[ExecutiveSummary] = None

    # --- Trazabilidad y Logs ---
    history: List[str] = Field(default_factory=list)
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    # Acepta str (Submissions) o int (RankPilot) para evitar quiebres:
    current_step: Union[str, int] = "" 
    next_node: str = "" # Usado por RankPilot para ruteo condicional
    errors: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)

    # ==========================================
    # VALIDADORES (Los Escudos de Producción)
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
    
    @field_validator("submission", mode="before")
    @classmethod
    def sanitize_php_garbage(cls, v: Optional[Any]) -> Optional[Any]:
        if isinstance(v, dict):
            buggy_fields = ["narratives", "individual_nominations", "team_dynamics"]
            for field in buggy_fields:
                if field in v and isinstance(v[field], dict) and "stdClass" in v[field]:
                    v[field] = {}
        return v

    @field_validator("new_answer", mode="before")
    @classmethod
    def sanitize_new_answer(cls, v: Any) -> Dict[str, str]:
        """El Null Killer de Laravel"""
        default = {"target_field": "", "question_text": "", "answer": ""}
        if not isinstance(v, dict):
            return default
        return {
            "target_field": str(v.get("target_field") or ""),
            "question_text": str(v.get("question_text") or ""),
            "answer": str(v.get("answer") or "")
        }