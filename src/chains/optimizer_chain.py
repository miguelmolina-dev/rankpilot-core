from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from pydantic import BaseModel, Field

# =========================================================
# 1. EL CEREBRO DE NARRATIVAS GLOBALES
# =========================================================
class OptimizedNarrative(BaseModel):
    what_sets_us_apart: str = Field(description="Optimized 'What Sets Us Apart' narrative.", default="")
    initiatives_and_innovation: str = Field(description="Optimized 'Initiatives' narrative.", default="")

narrative_prompt = ChatPromptTemplate.from_template(
    """
    SYSTEM: 
    You are an Elite Legal Ghostwriter. Your job is to rewrite the firm's general narrative sections to sound like a 'Band 1' (Top Tier) market leader.

    DIRECTORY RULES:
    {copywriting_guidelines}

    RAW NARRATIVE DATA:
    {narrative_json}

    INSTRUCTIONS:
    Rewrite the narrative to be a powerful, cohesive thesis of the firm's market dominance. 
    Focus on institutional depth, market positioning, and strategic vision.
    Do NOT hallucinate facts. Elevate the vocabulary to premium British/US corporate English.
    """
)
narrative_chain = narrative_prompt | get_llm(temperature=0.4).with_structured_output(OptimizedNarrative)

# =========================================================
# 2. EL ESPECIALISTA EN MATTERS (Casos y Transacciones)
# =========================================================
class OptimizedMatter(BaseModel):
    optimized_description: str = Field(description="The elite, restructured matter description.")

matter_prompt = ChatPromptTemplate.from_template(
    """
    SYSTEM: 
    You are a specialized Legal 'Matter' Editor. You transform dry, passive case descriptions into aggressive, 'Band 1' market-moving achievements.

    DIRECTORY RULES:
    {copywriting_guidelines}
    
    CONFIDENTIALITY STATUS: {confidential_status}
    (If True, focus purely on the legal mechanics, structural complexity, and monetary value. Redact or generalize specific client names if the raw text asks for it).

    RAW MATTER DATA:
    {matter_json}

    INSTRUCTIONS:
    1. RESTRUCTURE: Format the description into three clear, highly scannable paragraphs: 
       - The Commercial/Legal Challenge.
       - The Firm's Strategic Role/Maneuver.
       - The Market Impact/Value.
    2. TONE: Use active, powerful verbs (e.g., 'Spearheaded', 'Engineered', 'Neutralized', 'Architected'). Eliminate passive voice completely.
    3. FACTS: Retain all specific monetary values, jurisdictions, and dates. Do NOT invent data.
    4. LENGTH: Keep it punchy. Executives value density over length.
    """
)
matter_chain = matter_prompt | get_llm(temperature=0.3).with_structured_output(OptimizedMatter)

# =========================================================
# 3. EL CONDENSADOR DE SUMMARIES (Work Highlights)
# =========================================================
class OptimizedSummary(BaseModel):
    short_summary: str = Field(description="The condensed summary, maximum 40 words.")

summary_prompt = ChatPromptTemplate.from_template(
    """
    SYSTEM: 
    You are an extremely ruthless and efficient Legal Editor. Your task is to take long, verbose case descriptions and condense them into a single, punchy 1-2 sentence summary.

    CRITICAL RULES:
    1. LENGTH LIMIT: Maximum 40 words. Under no circumstances exceed this.
    2. FORMAT: Start directly with an active verb (e.g., "Advised [Client] on...", "Represented [Client] in...", "Defended [Client] against...").
    3. FOCUS: Keep ONLY the client name, the core transaction/dispute, and the primary legal action. Strip out all background fluff, marketing language, and secondary tasks.

    RAW TEXT TO CONDENSE:
    {raw_summary}

    INSTRUCTIONS:
    Extract the core legal action and format it into a tight, aggressive 40-word maximum summary.
    """
)
summary_chain = summary_prompt | get_llm(temperature=0.2).with_structured_output(OptimizedSummary)