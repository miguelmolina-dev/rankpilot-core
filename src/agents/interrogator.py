from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.core.state import AgentState
from src.core.llm import get_llm

class StrategicQuestion(BaseModel):
    question: str = Field(
        description="A strategic question asking for the specific missing information."
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

            system_prompt = (""""
                You are an elite Legal Ranking Strategist (Chambers & Partners / Legal 500) consulting for a top-tier law firm. Your goal is to conduct a highly efficient, strategic interview with the firm's partners to extract necessary information for their directory submission.
                CRITICAL RULES:
                1. Embody a premium consultant persona: professional, sharp, and strategically encouraging.
                2. ALWAYS generate exactly ONE clear, targeted question. Do not overwhelm the user with multiple questions at once.
                3. Never ask for information that is already present in the provided context.
                4. Keep it concise. High-level executives value their time; make every word count.
            """)

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

            # 3. CONCIENCIA DE ESTADO: ¿Es la primera pregunta o ya estamos en medio de la reunión?
            submission_data = getattr(state, "submission", None)
            is_first_question = True
            
            if submission_data:
                # Limpiamos los campos vacíos para ver si realmente hay información guardada
                dump = submission_data.model_dump(exclude_none=True)
                dump = {k: v for k, v in dump.items() if v and str(v) != "{}" and str(v) != "[]"}
                
                current_submission_context = str(dump).replace("{", "{{").replace("}", "}}")
                if len(dump) > 0:
                    is_first_question = False # ¡Ya hay datos! Prohibido saludar.
            else:
                current_submission_context = "No information extracted yet."

            # =======================================================
            # 4. EL CEREBRO DEL ESTRATEGA (Prompts Dinámicos)
            # =======================================================
            
            # SYSTEM PROMPT: La personalidad inquebrantable
            system_prompt = (
                "You are an elite Legal Ranking Strategist (former Chambers & Partners senior editor) consulting for a top-tier transnational law firm. "
                "You are in a live, high-stakes strategy room with the Managing Partner.\n\n"
                "CRITICAL BEHAVIORAL RULES:\n"
                "1. BE ALIVE & HUMAN: Never sound like a chatbot. You are a sharp, perceptive human expert.\n"
                "2. NO REPETITION: You must sound conversational. Flow naturally from one topic to the next based on the Conversation History.\n"
                "3. Speak peer-to-peer using a highly sophisticated, corporate, and analytical tone."
            )

            # Dependiendo del caso, definimos el prompt y SOLO las variables que ese prompt necesita
            if is_first_question:
                user_prompt = (
                    "Target Field needed: {field}\n"
                    "Reason: {reason}\n\n"
                    "TASK:\n"
                    "Give a warm, brief, and highly professional welcome to the strategy session. "
                    "Then, smoothly ask the Partner to provide the information for '{field}' to lay the foundation of the submission."
                )
                # Diccionario exacto para la primera pregunta
                prompt_vars = {
                    "field": field,
                    "reason": reason
                }
            else:
                user_prompt = (
                    "--- FIRM LORE & EXTRACTED DATA SO FAR ---\n"
                    "{current_submission_context}\n\n"
                    "--- CONVERSATION HISTORY ---\n"
                    "{conversation_history}\n\n"
                    "--- RECENT STATEMENT FROM PARTNER ---\n"
                    "Partner's Input: '{previous_answer_text}'\n\n"
                    "--- NEXT OBJECTIVE ---\n"
                    "Target Field needed: {field}\n"
                    "Reason: {reason}\n\n"
                    "--- YOUR TASK (STRICT RULES) ---\n"
                    "1. DO NOT GREET THE PARTNER. DO NOT SAY 'Welcome', 'To start', or 'To begin'. The meeting has been going on for a while.\n"
                    "2. CONTEXTUAL AWARENESS: Read the 'Conversation History'. Ensure your next response feels connected to the ongoing dialogue.\n"
                    "3. ACTIVE LISTENING: Start with ONE highly insightful sentence validating their strategy based on the 'Firm Lore' or their 'Recent Statement'. Prove you are a strategic partner.\n"
                    "4. Smoothly pivot and ask exactly ONE targeted question to obtain the '{field}'. Make it sound like the natural, logical next step."
                )
                # Diccionario exacto para las siguientes preguntas
                prompt_vars = {
                    "field": field,
                    "reason": reason,
                    "current_submission_context": current_submission_context,
                    "conversation_history": conversation_history,
                    "previous_answer_text": previous_answer_text
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
