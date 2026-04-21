from langgraph.graph import StateGraph, END
from typing import Literal

from src.core.state import AgentState

# --- ACTO 1: Captura de Datos (Submissions Core) ---
from src.agents.extractor import ingestion_node
from src.agents.classifier import classification_node
from src.agents.sanitizer import sanitizer_node
from src.agents.auditor import audit_node
from src.agents.interrogator import interrogator_node
from src.agents.answer_evaluator import process_answer_node 
from src.agents.scheduler import scheduler_node

# --- ACTO 2: Pulido y Ensamblaje (NUEVO) ---
# Usaremos un placeholder para importarlo cuando lo creemos
from src.agents.optimizer import optimize_node 
from src.agents.assembler import assembly_node

# --- ACTO 3: Diagnóstico Estratégico (RankPilot Engine) ---
from src.agents.snapshot_generator import snapshot_generator_node
from src.agents.executive_writer import executive_writer_node


def route_entry(state: AgentState) -> Literal["process_answer_node", "classification_node"]:
    """
    Ruteo de entrada:
    Si hay una respuesta del usuario, entramos a evaluar esa respuesta.
    Si es un inicio en frío, vamos a clasificar y extraer el PDF.
    """
    new_answer = getattr(state, "new_answer", {}) or {}
    if new_answer.get("answer"):
        return "process_answer_node"
    return "classification_node"

def route_after_audit(state: AgentState) -> Literal["interrogator_node", "optimize_node"]:
    """
    EL PUENTE ENTRE EL ACTO 1 Y EL ACTO 2:
    Si hay 'gaps', pausamos y preguntamos al usuario.
    Si hay 0 gaps (o si se fuerza la auditoría), pasamos a la fase de optimización.
    """
    gaps = getattr(state, "gaps", []) or []
    # Nota: Aquí podríamos agregar 'or state.config.get("force_audit")' si quieres ese botón
    if len(gaps) > 0:
        return "interrogator_node"
    
    # 0 Gaps: El submission está "crudo" pero completo. ¡A optimizar!
    return "optimize_node"


def build_workflow() -> StateGraph:
    """
    Construye la máquina de estados LangGraph (Arquitectura de 3 Actos).
    """
    workflow = StateGraph(AgentState)

    # ------------------------------------------
    # REGISTRO DE NODOS
    # ------------------------------------------
    # Acto 1
    workflow.add_node("classification_node", classification_node)
    workflow.add_node("ingestion_node", ingestion_node)
    workflow.add_node("process_answer_node", process_answer_node)
    workflow.add_node("sanitizer_node", sanitizer_node)
    workflow.add_node("audit_node", audit_node)
    workflow.add_node("interrogator_node", interrogator_node)
    
    # Acto 2
    workflow.add_node("optimize_node", optimize_node)
    workflow.add_node("assembly_node", assembly_node)
    
    # Acto 3
    workflow.add_node("snapshot_generator_node", snapshot_generator_node)
    workflow.add_node("scheduler_node", scheduler_node)
    workflow.add_node("executive_writer_node", executive_writer_node)

    # ------------------------------------------
    # DEFINICIÓN DE ARISTAS (EDGES) Y FLUJO
    # ------------------------------------------
    
    # PUNTO DE ENTRADA
    workflow.set_conditional_entry_point(
        route_entry,
        {
            "process_answer_node": "process_answer_node",
            "classification_node": "classification_node"
        }
    )

    # --- ACTO 1: EL BUCLE DE CAPTURA ---
    workflow.add_edge("classification_node", "ingestion_node")
    workflow.add_edge("ingestion_node", "sanitizer_node")
    workflow.add_edge("process_answer_node", "sanitizer_node")
    workflow.add_edge("sanitizer_node", "audit_node")

    # Condicional: ¿Seguimos preguntando o pasamos a optimizar?
    workflow.add_conditional_edges(
        "audit_node",
        route_after_audit,
        {
            "interrogator_node": "interrogator_node",  # Pausa el grafo
            "optimize_node": "optimize_node"           # Avanza al Acto 2
        }
    )
    workflow.add_edge("interrogator_node", END) # Laravel toma el control aquí

    # --- ACTO 2: GHOSTWRITER Y ENSAMBLAJE ---
    # El optimizador reescribe los textos crudos en lenguaje "Band 1"
    workflow.add_edge("optimize_node", "assembly_node")
    
    # El ensamblador crea el DOCX y lo guarda en output_base64
    workflow.add_edge("assembly_node", "snapshot_generator_node")

    # RankPilot evalúa el documento y saca Fortalezas y Debilidades (Blind spots)
    workflow.add_edge("snapshot_generator_node", "scheduler_node")

    # --- ACTO 3: DIAGNÓSTICO ESTRATÉGICO ---
    # RankPilot evalúa el documento final y saca el Score, Fortalezas y Debilidades
    workflow.add_edge("scheduler_node", "executive_writer_node")
    
    # Fin del proceso. Laravel recibe el JSON final con el Score, el Veredicto y el DOCX.
    workflow.add_edge("executive_writer_node", END)

    return workflow.compile()