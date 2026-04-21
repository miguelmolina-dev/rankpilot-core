import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm
from src.core.schemas import ChambersSubmission, Legal500Submission, LeadersLeagueSubmission

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
            new_path = f"{path}.{i}"
            long_strings.update(get_long_string_fields(item, new_path))
    elif isinstance(data, str) and len(data) > 50:
        long_strings[path] = data
    return long_strings

def apply_cleaned_field(data: Any, path: str, clean_text: str):
    """Recursively applies the cleaned text back to the specific dictionary path."""
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

# --- NODE IMPLEMENTATION ---
def sanitizer_node(state: AgentState) -> dict:
    """
    Sanitizer Node with Batching Logic:
    Processes fields in groups of 5 to prevent LLM output token limits and EOF errors.
    """
    updates = {"current_step": "sanitizer", "messages": []}

    submission_data = getattr(state, "submission", None)
    if not submission_data:
        return updates

    submission_dict = submission_data.model_dump(exclude_none=True)
    target_submission_type = getattr(state, "target_submission_type", "Legal500") or "Legal500"

    # 1. Identificar campos largos
    text_fields_to_clean = get_long_string_fields(submission_dict)
    if not text_fields_to_clean:
        updates["messages"].append("Sanitizer node: No long text fields found to clean.")
        return updates

    # --- LÓGICA DE BATCHING (Grupos de 5) ---
    items = list(text_fields_to_clean.items())
    batch_size = 8
    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    # Configuración de Guías Editoriales (desde YAML)
    taml_config = getattr(state, "config", {}) or {}
    custom_guidelines = taml_config.get("copywriting_guidelines", "No additional guidelines provided.")

    llm = get_llm(temperature=0.3)
    # Importante: Algunos modelos requieren max_tokens explícito para salidas largas
    if hasattr(llm, "max_tokens"):
        llm.max_tokens = 4000

    structured_llm = llm.with_structured_output(SanitizationBatch)

    system_prompt = (
        "You are an elite Legal Copywriter and Strategist working for a top-tier law firm.\n"
        "Your job is to transform raw, messy notes into persuasive, professional, partner-level prose.\n\n"
        "=========================================\n"
        "DIRECTORY-SPECIFIC COPYWRITING RULES:\n"
        f"{custom_guidelines}\n"
        "=========================================\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. ELEVATE THE TONE: Use high-end legal and business vocabulary. Be authoritative and punchy.\n"
        "2. STRUCTURE FOR SCANNABILITY: Use powerful paragraphs or short blocks. bold key terms using asterisks.\n"
        "3. STRIP THE JUNK: Remove URLs, internal notes, and filler.\n"
        "4. ZERO HALLUCINATION: Retain every fact (names, dates, values, jurisdictions).\n"
        "5. FOCUS ON IMPACT: Frame work as strategic market impact (e.g., 'first to market').\n"
        "6. FIRM-FIRST PERSPECTIVE: Anchor arguments to the firm's overall dominance.\n"
        "7. MARKDOWN: Use ONLY double asterisks for bolding (e.g. **Firm Name**). No other markdown."
    )

    total_cleaned = 0
    for i, batch in enumerate(batches):
        # Crear el contexto de datos "sucios" para este lote
        dirty_data_context = "\n".join([f"KEY: {k}\nTEXT: {v}\n---" for k, v in batch])
        
        user_prompt = (
            f"### BATCH {i+1} of {len(batches)} ###\n"
            "Clean and rewrite the following fields according to the rules:\n\n"
            f"{dirty_data_context}\n\n"
            "Return the list of rewritten fields. Ensure 'field_key' perfectly matches the provided KEY."
        )

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])
            
            chain = prompt | structured_llm
            # El invoke va vacío porque las variables ya están inyectadas en el prompt template
            output = chain.invoke({}) 

            if output and output.cleaned_fields:
                for clean_item in output.cleaned_fields:
                    apply_cleaned_field(submission_dict, clean_item.field_key, clean_item.sanitized_text)
                    total_cleaned += 1
            
        except Exception as batch_error:
            # Si un lote falla (por ejemplo, por contenido sensible o error de red), 
            # el sistema continúa con el siguiente lote para salvar el resto de la información.
            print(f"--- [WARNING] Failed to sanitize batch {i+1}: {batch_error} ---")
            updates["messages"].append(f"Sanitizer: Batch {i+1} failed to process. Keeping raw data for these fields.")

    # 3. Re-validar a través de Pydantic y actualizar el estado
    try:
        if target_submission_type == "Legal500":
            updates["submission"] = Legal500Submission(**submission_dict)
        elif target_submission_type == "LeadersLeague":
            updates["submission"] = LeadersLeagueSubmission(**submission_dict)
        else:
            updates["submission"] = ChambersSubmission(**submission_dict)
            
        updates["messages"].append(f"Sanitizer node: Successfully sanitized {total_cleaned} fields across {len(batches)} batches.")
    except Exception as e:
        print(f"--- [ERROR] Schema validation failed after sanitization: {e} ---")
        updates["messages"].append("Sanitizer: Schema validation failed. Returning original data.")

    return updates