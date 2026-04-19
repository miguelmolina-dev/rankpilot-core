import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import ChambersSubmission, Legal500Submission

# --- STRUCTURED OUTPUT MODELS ---
class CleanedField(BaseModel):
    field_key: str = Field(description="The exact key/path of the field being cleaned.")
    sanitized_text: str = Field(description="The fully cleaned and formatted text.")

class SanitizationBatch(BaseModel):
    cleaned_fields: List[CleanedField] = Field(description="List of fields that have been sanitized.")

# --- RECURSIVE HELPERS ---
def get_long_string_fields(data: Any, path: str = "") -> Dict[str, str]:
    """Recursively finds all string fields longer than 50 characters to sanitize using dot notation."""
    long_strings = {}
    if isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{path}.{k}" if path else k
            long_strings.update(get_long_string_fields(v, new_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            # FIX: Use a dot for array indices instead of brackets (e.g., matters.0.matter_description)
            new_path = f"{path}.{i}" if path else str(i)
            long_strings.update(get_long_string_fields(item, new_path))
    elif isinstance(data, str) and len(data) > 50:
        long_strings[path] = data
    return long_strings

def apply_cleaned_field(data: Any, path: str, clean_text: str):
    """Recursively applies the cleaned text back to the specific dictionary path."""
    # FIX: Now we can just safely split by dots
    keys = path.split(".")
    
    current = data
    for key in keys[:-1]:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            current = current[int(key)]
            
    final_key = keys[-1]
    if isinstance(current, dict):
        current[final_key] = clean_text
    elif isinstance(current, list):
        current[int(final_key)] = clean_text


def sanitizer_node(state: AgentState) -> dict:
    """
    Sanitizer Node:
    Scans the extracted submission for raw, messy text blocks.
    Uses an LLM to strip web artifacts, formatting errors, and metadata.
    """
    updates = {"current_step": "sanitizer", "messages": []}

    submission_data = getattr(state, "submission", None)
    if not submission_data:
        return updates

    submission_dict = submission_data.model_dump(exclude_none=True)
    target_submission_type = getattr(state, "target_submission_type", "Legal500") or "Legal500"

    # 1. Hunt down the messy text (Saves massive amounts of tokens)
    text_fields_to_clean = get_long_string_fields(submission_dict)
    
    if not text_fields_to_clean:
        updates["messages"].append("Sanitizer node: No long text fields found to clean.")
        return updates

    # Convert to a readable string for the LLM
    dirty_data_context = "\n".join([f"KEY: {k}\nTEXT: {v}\n---" for k, v in text_fields_to_clean.items()])

    try:
        # We can increase the temperature slightly (e.g., 0.2 or 0.3) to allow for better phrasing and vocabulary.
        llm = get_llm(temperature=0.3)
        structured_llm = llm.with_structured_output(SanitizationBatch)

        system_prompt = (
            "### ROLE ###\n"
            "You are an elite English-language Legal Copywriter and Strategist for a top-tier global law firm. "
            "Your mission is to transform messy, multi-language, or raw internal notes into authoritative, "
            "partner-level submission prose in STRICT PROFESSIONAL ENGLISH.\n\n"
            
            "### CRITICAL COPYWRITING INSTRUCTIONS ###\n"
            "1. MANDATORY ENGLISH OUTPUT: Regardless of the input language (Spanish, Portuguese, etc.), you MUST "
            "output the sanitized text ONLY in English. Use high-end British or American legal vocabulary suitable for Legal500/Chambers.\n"
            "2. ELEVATE THE TONE: Rewrite the text to be authoritative and commercially aware. Instead of 'we do FinTech', "
            "use 'we provide strategic counsel navigating the intersection of complex regulatory frameworks and digital innovation'.\n"
            "3. STRUCTURE FOR SCANNABILITY: Use powerful paragraphs or bolded sections (using capital letters since Markdown is forbidden).\n"
            "4. STRIP THE JUNK: Delete raw URLs, internal ranking notes, and conversational filler.\n"
            "5. PRESERVE ALL FACTS: Retain every concrete fact (names, dates, values, jurisdictions) accurately.\n"
            "6. THE FIRM-FIRST PERSPECTIVE: For 'rankings_feedback', always advocate for the firm's market position "
            "in the first-person plural ('We believe...'), using partners as supporting evidence.\n"
            "7. STRICTLY NO MARKDOWN: Output pure, clean, plain text ONLY. Do NOT use asterisks (**), hashtags (#), or underscores (_). "
            "Use standard punctuation and capital letters to separate sections."
        )

        user_prompt = (
            "Here are the specific fields and their raw text that need to be rewritten for the final submission:\n\n"
            f"{dirty_data_context}\n\n"
            "Return the list of rewritten fields. Make sure the 'field_key' perfectly matches the KEY provided."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt),
        ])

        chain = prompt | structured_llm
        output = chain.invoke({})

        # 2. Patch the clean data back into the dictionary
        for clean_item in output.cleaned_fields:
            apply_cleaned_field(submission_dict, clean_item.field_key, clean_item.sanitized_text)

        updates["messages"].append(f"Sanitizer node: Successfully sanitized {len(output.cleaned_fields)} text fields.")

        # 3. Re-validate through Pydantic to ensure the schema is still perfect
        if target_submission_type == "Legal500":
            updates["submission"] = Legal500Submission(**submission_dict)
        else:
            updates["submission"] = ChambersSubmission(**submission_dict)

    except Exception as e:
        import traceback
        traceback.print_exc()
        updates["messages"].append(f"Sanitizer node failed: {e}. Proceeding with raw data.")

    return updates