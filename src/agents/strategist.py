from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState

# --- 1. Define the Output Schema ---
class MilestoneSchema(BaseModel):
    category: str = Field(description="Category: Narrative, Quantitative, or Leadership")
    action_title: str = Field(description="Clear, 5-word headline for the task")
    why_it_matters: str = Field(description="The strategic 'Elite Tier' justification")
    technical_instruction: str = Field(description="Step-by-step guide for the associate")
    priority_level: int = Field(description="1 (Critical) to 5 (Low)")
    days_before_deadline: int = Field(description="Days remaining when this task should be done")

class StrategistResponse(BaseModel):
    evolution_path: List[MilestoneSchema] = Field(description="The 5-step strategic roadmap")
    overall_score: int = Field(description="Current submission health score (0-100)")
    risk_level: str = Field(description="Critical, Moderate, or Low")
    strategic_verdict: str = Field(description="3-line verdict for the executive modal")
    audit_letter_markdown: str = Field(description="The full professional letter for the Managing Partner")

# --- 2. The High-Fidelity Prompt ---

strategist_prompt = ChatPromptTemplate.from_template(
    """
    SYSTEM: 
    You are the "Chief Strategy Officer" specialized in Global Legal Rankings (Chambers & Partners / Legal 500). 
    Your objective is not just to fill out a form, but to architect a narrative of market dominance.
    
    OPERATIONAL CONTEXT:
    - Submission Deadline: {submission_deadline}
    - Region & Practice Area: {region} / {practice_area}
    - Current Evidence: {raw_text}
    - Identified Gaps: {gaps}
    
    CHAIN-OF-THOUGHT PROCESS:
    1. ANALYZE remaining time: Calculate urgency based on the current date and the deadline.
    2. AUDIT the narrative: What story is the firm currently telling? (e.g., "We are high-volume processors" vs. "We are leaders in high-stakes complex litigation").
    3. DETECT the "Missing Value": Based on the {practice_area}, identify themes researchers are rewarding this year (e.g., ESG, Cybersecurity, Cross-border Arbitration).
    4. BALANCE the team: Review for partner power concentration and suggest strategic delegation to showcase depth.

    OUTPUT INSTRUCTIONS (Generate exactly 5 milestones):
    Each step must follow this "High-Value" structure:
    
    - CATEGORY: [Narrative Strategy / Quantitative Density / Leadership Balance / Critical Volume]
    - TITLE: Concrete and technical action.
    - WHY IT MATTERS: The business value. Why does this trigger a Tier (Band) elevation?
    - TECHNICAL INSTRUCTION: The detailed "How-to" for the associate lawyer.
    - DAYS BEFORE DEADLINE: When this must be completed.
    - PRIORITY: (1 to 5, where 1 is critical).

    GOLDEN RULE: 
    If the firm has fewer than 20 matters, Priority 1 MUST always be 'Content Curation' to reach the limit, specifying exactly what TYPE of cases to look for to impress the researcher.
    
    STYLE: 
    Direct, sophisticated, authoritative, and 100% grounded in the evidence found in {raw_text}.
    """
)

# --- 3. The Node Function ---
def strategist_agent(state: AgentState) -> Dict[str, Any]:
    print("--- [NODE] Executing Strategic Scheduler ---")
    
    # Initialize LLM with Structured Output
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    structured_llm = llm.with_structured_output(StrategistResponse)
    
    # Prepare Context
    metadata = state.get("metadata", {})
    prompt = ChatPromptTemplate.from_messages([
        ("system", strategist_prompt),
        ("human", "Submission Data: {raw_text}")
    ])
    
    # Chain execution
    chain = prompt | structured_llm
    
    response = chain.invoke({
        "deadline": metadata.get("submission_deadline", "Unknown"),
        "practice_area": metadata.get("practice_area", "General"),
        "region": metadata.get("region", "Global"),
        "gaps": state.get("positioning_core", {}).get("signals", []),
        "raw_text": state.get("raw_text", "")[:15000] # Buffer for context window
    })

    # Return the updates for the state
    return {
        "evolution_path": [m.model_dump() for m in response.evolution_path],
        "executive_summary": {
            "overall_score": response.overall_score,
            "risk_level": response.risk_level,
            "strategic_verdict": response.strategic_verdict,
            "top_differentiators": [m.action_title for m in response.evolution_path[:2]],
            "audit_letter_markdown": response.audit_letter_markdown
        }
    }