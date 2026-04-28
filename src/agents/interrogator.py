from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm

class StrategicQuestion(BaseModel):
    question: str = Field(
        description="The complete verbal response to the Partner. It MUST include your conversational clarification or validation FIRST, followed immediately by the targeted question."
    )

def interrogator_node(state: AgentState) -> dict:
    """
    Interrogator Node:
    Generates dynamic, strategic questions for the fields marked as null or missing (gaps)
    using an LLM.
    """
    updates = {"current_step": "interrogator", "messages": []}

    gaps = getattr(state, "gaps", []) or []
    question = ""
    field = ""

    if gaps:
        try:
            llm = get_llm(temperature=0.2)
            structured_llm = llm.with_structured_output(StrategicQuestion)

            # =======================================================
            # THE MASTER SYSTEM PROMPT (La Biblia del Consultor)
            # =======================================================
            system_prompt = (
                "[ROLE & CONTEXT]\n"
                "You are an elite Legal Ranking Strategist (former Chambers & Partners/Legal 500 senior editor) consulting for a top-tier transnational law firm. "
                "You are in a live, high-stakes strategy room with the Managing Partner.\n\n"
                "[OBJECTIVE]\n"
                "Conduct a highly efficient, strategic interview to extract necessary information for their directory submission. "
                "ALWAYS generate exactly ONE clear, targeted question. Do not overwhelm the user with multiple questions at once.\n\n"
                "[THE FORBIDDEN LEXICON - STRICTLY ENFORCED]\n"
                "You will receive system variables representing missing fields (e.g., 'publishable_matters.0.D3_matter_value' or 'identity.firm_name'). "
                "THESE ARE INTERNAL DATABASE LABELS FOR YOUR EYES ONLY. UNDER NO CIRCUMSTANCES are you allowed to utter them to the Partner.\n"
                "❌ YOU MUST NEVER USE:\n"
                "- Array indices or numbers indicating list position (e.g., NEVER say 'Matter 1', 'first confidential matter', 'Client 0').\n"
                "- Alphanumeric section codes from the form (e.g., NEVER say 'D3', 'E4', 'B2', 'A1').\n"
                "- System field names (e.g., NEVER say 'matter_value', 'publishable_matters', 'identity.firm_name').\n"
                "- Robotic phrasing (e.g., NEVER say 'Please provide the information for...', 'The target field needed is...').\n\n"
                "[TRANSLATION & REFERENCING GUIDE]\n"
                "Translate the system label into natural, executive language using context clues:\n"
                "- BAD: 'Provide the identity.firm_name.' -> GOOD: 'To lay the right foundation, could you please confirm the official registered name of the firm?'\n"
                "- BAD: 'We need the department_info.metrics.partners_count_50_percent_plus.' -> GOOD: 'To demonstrate the depth of our bench, how many partners dedicate at least 50% of their time strictly to this practice?'\n"
                "- BAD: 'Could you provide the D3 matter value for Publishable Matter 1?' -> GOOD: 'To fully capture the scale of this transaction, are we able to disclose the financial value or size of the deal?'\n\n"
                "[CRITICAL BEHAVIORAL RULES & TONE]\n"
                "1. BE ALIVE & HUMAN: Never sound like a chatbot. You are a sharp, perceptive human expert.\n"
                "2. NO REPETITION: Flow naturally. Make it sound like a high-level strategic discussion.\n"
                "3. Speak peer-to-peer using a highly sophisticated, corporate, and analytical tone.\n"
                "4. Keep it concise. High-level executives value their time; make every word count."
            )

            input_type = getattr(state, "input_document_type", "unknown")
            first_gap = gaps[0]
            field = first_gap.get('field', 'unknown')
            reason = first_gap.get('reason', 'Missing information.')
            
            # 2. Rescatar la respuesta anterior (Si la borró el nodo anterior, miraremos el contexto global)
            previous_answer_obj = getattr(state, "new_answer", {})
            previous_answer_text = previous_answer_obj.get("answer", "") if previous_answer_obj else ""

            history_data = getattr(state, "history", [])
            if history_data and isinstance(history_data, list):
                # Unimos los últimos 6 intercambios (para no desbordar tokens)
                conversation_history = "\n".join(history_data[-6:])
            else:
                conversation_history = "No previous conversation. This is the beginning."

            # 3. CONCIENCIA DE ESTADO: ¿Es la primera vez que le hablamos al usuario?
            history_data = getattr(state, "history", [])
            previous_answer_text = getattr(state, "new_answer", {}).get("answer", "").strip()
            
            # 🚨 LA CLAVE: Si el usuario mandó un texto, YA NO es la primera interacción.
            is_first_interaction = (len(history_data) == 0) and (not previous_answer_text)

            submission_data = getattr(state, "submission", None)
            if submission_data:
                # Limpiamos los campos vacíos para ver la "carne" de lo que se extrajo
                dump = submission_data.model_dump(exclude_none=True)
                dump = {k: v for k, v in dump.items() if v and str(v) != "{}" and str(v) != "[]"}
                current_submission_context = str(dump).replace("{", "{{").replace("}", "}}")
            else:
                current_submission_context = "No information extracted yet."

            input_type = getattr(state, "input_document_type", "unknown")

            # =======================================================
            # 4. EL CEREBRO DEL ESTRATEGA (Prompts Dinámicos)
            # =======================================================

            is_matter_request = "matters" in field.lower()
            matter_instruction = ""

            if is_matter_request:
                try:
                    index = int(field.split(".")[1]) + 1 
                    matter_instruction = (
                        f"\n\n[CRITICAL OVERRIDE: NEW MATTER REQUIRED]\n"
                        f"You must ask the Partner to introduce a COMPLETELY NEW, unmentioned client and case/transaction to demonstrate the firm's volume.\n"
                        f"DO NOT ask for more details about the clients already listed in the 'Extracted Firm Data'."
                    )
                except:
                    matter_instruction = "\n\n[CRITICAL OVERRIDE: NEW MATTER REQUIRED]\nAsk for a NEW, DIFFERENT case/transaction. Do not ask about previous cases."
            
            # SYSTEM PROMPT: La Biblia del Consultor de Élite
            system_prompt = (
                "[ROLE & CONTEXT]\n"
                "You are a world-class Legal Ranking Strategist (former Senior Editor at Chambers & Partners and The Legal 500). "
                "You are currently sitting in a boardroom consulting face-to-peer with the Managing Partner of a top-tier transnational law firm.\n\n"
                "[OBJECTIVE]\n"
                "Ask a highly strategic question to obtain missing information for their directory submission. Frame the request not as filling out a form, "
                "but as capturing critical evidence needed to secure a Band 1 ranking.\n\n"
                "[THE FORBIDDEN LEXICON - STRICTLY ENFORCED]\n"
                "You will receive system variables representing the missing field (e.g., 'publishable_matters.0.D3_matter_value' or 'identity.firm_name'). "
                "THESE ARE INTERNAL DATABASE LABELS FOR YOUR EYES ONLY. UNDER NO CIRCUMSTANCES are you allowed to utter them to the Partner.\n"
                "❌ YOU MUST NEVER USE:\n"
                "- Array indices or numbers indicating list position (e.g., NEVER say 'Matter 1', 'first confidential matter', 'Client 0').\n"
                "- Alphanumeric section codes from the form (e.g., NEVER say 'D3', 'E4', 'B2', 'A1').\n"
                "- System field names (e.g., NEVER say 'matter_value', 'publishable_matters', 'identity.firm_name').\n"
                "- Robotic phrasing (e.g., NEVER say 'Please provide the information for...', 'The target field needed is...').\n\n"
                "[TRANSLATION & REFERENCING GUIDE]\n"
                "Instead of using the system labels, you MUST translate the request into natural, executive language using context clues from the conversation:\n"
                "- BAD: 'Could you provide the D3 matter value for Publishable Matter 1 (Doopla)?'\n"
                "- GOOD: 'To fully capture the scale of the Doopla transaction, are we able to disclose the financial value or size of the deal?'\n"
                "- BAD: 'We need the E4 cross border jurisdictions for the Confidential Digital Asset case.'\n"
                "- GOOD: 'Regarding the highly sensitive Digital Asset platform launch, could you specify which international jurisdictions were involved to highlight our cross-border capabilities?'\n\n"
                "[TONE & STYLE]\n"
                "- Speak peer-to-peer using a sophisticated, corporate, and analytical tone.\n"
                "- Keep it conversational but concise. High-level executives value their time; make every word count."
            )

            # --- RAMIFICACIÓN DE PROMPTS SEGÚN EL ESCENARIO ---
            
            if is_first_interaction and input_type in ["docx", "pdf", "raw_text"] and len(current_submission_context) > 20:
                # RAMA 1: EL "FAN SERVICE"
                user_prompt = (
                    "--- EXTRACTED FIRM DATA SO FAR ---\n"
                    "{current_submission_context}\n\n"
                    "--- INTERNAL SYSTEM TARGET (DO NOT SAY THIS OUT LOUD) ---\n"
                    "Target Field needed: {field}\n"
                    "Reason: {reason}\n\n"
                    "--- YOUR TASK (THE FAN SERVICE HOOK) ---\n"
                    "1. The Partner just submitted their initial draft for your review.\n"
                    "2. Start with a 1-2 sentence strategic mini-audit: Validate their work. Explicitly mention a specific strength, impressive client, or standout matter you see in the 'Extracted Firm Data' to prove you read it and are impressed.\n"
                    "3. Make them feel recognized as a top-tier firm.\n"
                    "4. Then, seamlessly pivot to ask for the missing information. Remember the FORBIDDEN LEXICON: translate '{field}' into a natural, strategic question."
                )
                prompt_vars = {
                    "field": field,
                    "reason": reason,
                    "current_submission_context": current_submission_context
                }

            elif is_first_interaction:
                # RAMA 2: START FROM SCRATCH
                user_prompt = (
                    "--- INTERNAL SYSTEM TARGET (DO NOT SAY THIS OUT LOUD) ---\n"
                    "Target Field needed: {field}\n"
                    "Reason: {reason}\n\n"
                    "--- YOUR TASK ---\n"
                    "Give a warm, brief, and highly professional welcome to the strategy session. "
                    "Then, smoothly ask the Partner to provide the information needed to lay the foundation of our submission. Remember the FORBIDDEN LEXICON: translate '{field}' into a natural human question."
                )
                prompt_vars = {"field": field, "reason": reason}

            else:
                # RAMA 3: EN MEDIO DE LA REUNIÓN (CONVERSACIÓN ACTIVA)
                conversation_history = "\n".join(history_data[-6:]) if history_data else "No previous conversation."
                
                user_prompt = (
                    "--- FIRM LORE & EXTRACTED DATA SO FAR ---\n"
                    "{current_submission_context}\n\n"
                    "--- CONVERSATION HISTORY ---\n"
                    "{conversation_history}\n\n"
                    "--- RECENT STATEMENT FROM PARTNER ---\n"
                    "Partner's Input: '{previous_answer_text}'\n\n"
                    "--- INTERNAL SYSTEM TARGET (DO NOT SAY THIS OUT LOUD) ---\n"
                    "Target Field needed: {field}\n"
                    "Reason: {reason}\n\n"
                    "{matter_instruction}\n\n"
                    "--- YOUR TASK (STRICT RULES) ---\n"
                    "1. DO NOT GREET THE PARTNER. The meeting has been going on for a while.\n"
                    "2. CLARIFICATION & ACTIVE LISTENING: If the Partner's Input is a question or shows confusion (e.g. asking 'What do you mean?'), YOU MUST ANSWER THEIR QUESTION directly and briefly based on directory standards. Do this FIRST.\n"
                    "3. Smoothly pivot and ask exactly ONE targeted question to obtain the missing information.\n"
                    "4. Remember the FORBIDDEN LEXICON: Translate '{field}' into a conversational request. Do not use array numbers or section codes.\n"
                    "5. Your final output MUST combine BOTH the answer to their doubt AND your new question into a single, natural paragraph."
                )
                prompt_vars = {
                    "field": field,
                    "reason": reason,
                    "current_submission_context": current_submission_context,
                    "conversation_history": conversation_history,
                    "previous_answer_text": previous_answer_text,
                    "matter_instruction": matter_instruction
                }

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt),
            ])
            
            chain = prompt | structured_llm
            
            # Pasamos las variables dinámicas
            result = chain.invoke(prompt_vars)

            question = result.question

        except Exception as e:
            # Fallback to simple logic if LLM fails (e.g., no API key in tests)
            updates["messages"].append(f"LLM generation failed: {e}. Falling back to simple questions.")
            first_gap = gaps[0]
            field = first_gap.get("field", "unknown")
            question = f"We are missing information for '{field}'. Could you provide details?"

    updates["new_answer"] = {
        "question_text": question,
        "answer": "",
        "target_field": field  # NEW: Pass the field forward
    }
    updates["questions"] = [question]
    # Better logging to see exactly what gap we are targeting
    updates["messages"].append(f"Interrogator node: Generated question for gap in field '{field}' and paused for Laravel.")

    return updates
