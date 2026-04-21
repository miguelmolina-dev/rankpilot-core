from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from langchain_core.output_parsers import PydanticOutputParser

# 1. Define the Schema for the Output (The Roadmap)
class MilestoneSchema(BaseModel):
    category: str = Field(description="Category: Narrative Strategy, Quantitative Density, Leadership Balance, or Volume Expansion")
    action_title: str = Field(description="A 5-8 word technical headline for the milestone")
    why_it_matters: str = Field(description="Strategic justification for Tier/Band elevation based on ranking criteria")
    technical_instruction: str = Field(description="Step-by-step 'How-to' for the associate lawyer to execute")
    priority_level: int = Field(description="Integer from 1 (Critical) to 5 (Standard)")
    # --- CAMBIO: Nueva variable para la fecha exacta ---
    target_completion_date: str = Field(description="Exact formatted calendar date (e.g., 'November 15, 2026') by which this must be completed.")

class SchedulerResponse(BaseModel):
    evolution_path: List[MilestoneSchema] = Field(description="A list of exactly 5 strategic milestones")

parser = PydanticOutputParser(pydantic_object=SchedulerResponse)

STRATEGIC_SCHEDULER_PROMPT = ChatPromptTemplate.from_template(
    """
    SYSTEM: 
    You are the "Lead Architect & Project Manager" for International Legal Rankings. 
    Your mission is to engineer a 5-step strategic roadmap that guarantees a Band 1/Tier 1 evaluation.
    
    OPERATIONAL CONTEXT:
    - Today's Date: {current_date}
    - Deadline: {submission_deadline}
    - Location/Area: {location} / {practice_area}
    - Found Gaps: {gaps}
    - Blind Spots: {blind_spots}
    - Evidence: {submission_json}

    CHAIN-OF-THOUGHT INSTRUCTIONS:
    1. ANALYZE TEMPORAL URGENCY: Calculate the remaining window between Today's Date and the Deadline. 
    2. CONTENT VOLUME CHECK: If the matter count is below 20, Step 1 and 2 MUST prioritize "Content Discovery".
    3. STRATEGIC POSITIONING: Identify the "Market Leader" signal for {practice_area}.
    4. SEQUENCING: Order steps chronologically from "Heavy Lifting" (Gathering data) to "Surgical Refinement" (Polishing text).

    OUTPUT REQUIREMENTS (5 Milestones):
    For each milestone, you MUST provide:
    - CATEGORY: [Strategic Narrative, Quantitative Density, Leadership Balance, or Volume Expansion].
    - ACTION TITLE: A technical, professional headline.
    - WHY IT MATTERS: Explain the "Tier Elevation" logic.
    - TECHNICAL INSTRUCTION: A specific "How-to" for the Associate Lawyer.
    - TARGET COMPLETION DATE: Calculate an exact, formatted calendar date (e.g., 'October 30, 2026') for when this milestone must be completed. Space these dates logically between Today's Date and the Deadline.
    - PRIORITY: 1 (Critical) to 5 (Standard).

    STYLE: 
    Cold, analytical, and authoritative. Use the names of partners and cases found in {submission_json}.
    {format_instructions}
    """
)

llm = get_llm(temperature=0.1) 

scheduler_chain = (
    STRATEGIC_SCHEDULER_PROMPT.partial(format_instructions=parser.get_format_instructions()) 
    | llm 
    | parser
)