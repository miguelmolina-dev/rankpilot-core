from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from pydantic import BaseModel, Field
from typing import List
from langchain_core.output_parsers import PydanticOutputParser

class PracticeModel(BaseModel):
    label: str = Field(description="The formal name of the practice type.")
    definition: str = Field(description="A concise technical definition.")

class PositioningTier(BaseModel):
    label: str = Field(description="One of: 'Elite', 'Consolidated', or 'Market Member'.")
    explanation: str = Field(description="Professional justification for the assigned tier.")

class BlindSpot(BaseModel):
    issue: str = Field(description="A short title for the identified gap.")
    description: str = Field(description="A detailed explanation of why this is a risk.")

# --- ACTUALIZADO: Consolidamos todo en el Snapshot Final ---
class FinalSnapshot(BaseModel):
    practice_model: PracticeModel = Field(description="The formal name and technical definition.")
    confidence_score: float = Field(description="Value between 0.0 and 1.0 based on evidence depth.")
    signals: List[str] = Field(description="Exactly 3 specific evidence-backed signals (e.g., $$$ values, landmark precedents).")
    positioning_tier: PositioningTier = Field(description="Elite, Consolidated, or Market Member.")
    blind_spots: List[BlindSpot] = Field(description="Exactly 4 high-stakes technical gaps.")
    competitive_advantage: List[str] = Field(description="Top 2 'Elite' signals.")

parser = PydanticOutputParser(pydantic_object=FinalSnapshot)

snapshot_prompt = ChatPromptTemplate.from_template(
    """
    SYSTEM: 
    You are the "Lead Auditor" for Global Legal Rankings. You are cold, analytical, and impossible to impress. 
    Your mission is to strip away the marketing fluff and expose the raw technical standing of this submission.
    
    =========================================
    DIRECTORY-SPECIFIC EVALUATION CRITERIA:
    You MUST judge this submission against these strict rules:
    {editorial_rules}
    =========================================
    
    GROUNDING MANDATE: 
    If it is not in the submission_json or history, it DOES NOT EXIST. 
    Do not hallucinate complexity. If the submission violates the evaluation criteria above (e.g. overclaiming), penalize the tier and add it as a Blind Spot.

    AUDIT PARAMETERS:
    - Practice Area: {practice_area}
    - Optimized Submission Data: {submission_json}
    - Supplemental Evidence (Q&A): {history}

    PHASE 1: THE TECHNICAL CORE
    - Define the 'Practice Model' based on the complexity of matters. 
    - Is this 'High-End Specialty', 'Commoditized Service', or 'Strategic Advisory'?
    - Extract 3 hard evidence signals (deals, precedents, $$$).

    PHASE 2: THE TIER VERDICT
    - Assign a Tier: [Elite / Consolidated / Market Member].
    - JUSTIFICATION: Compare the evidence against the Directory Criteria. 

    PHASE 3: THE INVISIBLE RISKS (4 Blind Spots)
    Identify exactly 4 technical gaps that an investigator would use to reject a Band 1 ranking.
    Focus on violations of the Directory Criteria, Lack of Quantitative Depth, Missing Friction, or Weak Cohesion.

    PHASE 4: THE WEAPONS (2 Competitive Advantages)
    Identify exactly 2 reasons why this firm is a threat to the market based on the evidence.

    TONE: Surgical, objective, authoritative.
    
    {format_instructions}
    """
)

llm = get_llm(temperature=0.2)
snapshot_chain = (
    snapshot_prompt.partial(format_instructions=parser.get_format_instructions())
    | llm
    | parser
)