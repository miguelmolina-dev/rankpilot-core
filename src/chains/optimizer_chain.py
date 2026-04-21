from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from pydantic import BaseModel, Field
from typing import List
from langchain_core.output_parsers import PydanticOutputParser

class OptimizedMatter(BaseModel):
    matter_id: int = Field(description="The index/ID of the matter being optimized")
    optimized_description: str = Field(description="The rewritten, Elite-level description.")

class OptimizedNarrative(BaseModel):
    best_known_for: str = Field(description="Rewritten Department Best Known For narrative.")

class OptimizerResponse(BaseModel):
    matters: List[OptimizedMatter] = Field(description="List of optimized matters.")
    narratives: OptimizedNarrative = Field(description="Optimized department narratives.")

parser = PydanticOutputParser(pydantic_object=OptimizerResponse)

optimizer_prompt = ChatPromptTemplate.from_template(
    """
    SYSTEM: 
    You are an Elite Legal Ghostwriter and Editor. A law firm has provided raw data for their submission. 
    Your job is to rewrite their narrative sections to sound like a 'Band 1' (Top Tier) market leader.

    =========================================
    DIRECTORY-SPECIFIC EDITORIAL RULES:
    {copywriting_guidelines}
    =========================================

    RULES FOR REWRITING (OVERRIDE WITH ABOVE IF CONFLICT):
    1. Focus on 'Friction': Highlight cross-border complexities, novel legal arguments, and high-stakes commercial impact.
    2. Tone: Professional, sophisticated, British English. 
    3. Retain Facts: DO NOT alter client names, partner names, jurisdictions, or monetary values. Only elevate the prose.

    RAW SUBMISSION DATA:
    {submission_json}

    INSTRUCTIONS:
    1. Read the Narratives section and rewrite it to be a powerful, cohesive thesis of the firm's market dominance, STRICTLY following the Editorial Rules.
    2. Read every Matter Description. Rewrite them to clearly structure: The Challenge, The Firm's Role, and The Impact.
    
    {format_instructions}
    """
)

llm = get_llm(temperature=0.4)
optimizer_chain = optimizer_prompt.partial(format_instructions=parser.get_format_instructions()) | llm | parser