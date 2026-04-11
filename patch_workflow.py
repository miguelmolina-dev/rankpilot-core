with open("src/core/workflow.py", "r") as f:
    content = f.read()

content = content.replace(
"""from src.agents.extractor import ingestion_node
from src.agents.classifier import classification_node
from src.agents.auditor import audit_node
from src.agents.interrogator import interrogator_node
from src.agents.assembler import assembly_node""",
"""from src.agents.extractor import ingestion_node
from src.agents.classifier import classification_node
from src.agents.auditor import audit_node
from src.agents.interrogator import interrogator_node
from src.agents.assembler import assembly_node
from src.agents.updater import update_node""")

content = content.replace(
"""def route_after_interrogator(state: AgentState) -> Literal["audit_node"]:
    \"\"\"
    After user answers questions (handled outside or mocked here),
    we re-audit.
    \"\"\"
    # In a real app, we wait for user input. Here we just loop back to audit
    return "audit_node"

def build_workflow(checkpointer=None, interrupt_before=None) -> StateGraph:""",
"""def route_entry(state: AgentState) -> Literal["update_node", "ingestion_node"]:
    \"\"\"
    If new_answer has an answer, we route to update_node.
    Otherwise, we route to ingestion_node (initial start).
    \"\"\"
    new_answer = state.get("new_answer", {})
    if new_answer.get("answer"):
        return "update_node"
    return "ingestion_node"

def build_workflow(checkpointer=None, interrupt_before=None) -> StateGraph:""")

content = content.replace(
"""    # Add nodes
    workflow.add_node("ingestion_node", ingestion_node)
    workflow.add_node("classification_node", classification_node)
    workflow.add_node("audit_node", audit_node)
    workflow.add_node("interrogator_node", interrogator_node)
    workflow.add_node("assembly_node", assembly_node)

    # Set Entry Point
    workflow.set_entry_point("ingestion_node")

    # Define simple linear flow for early steps
    workflow.add_edge("ingestion_node", "classification_node")
    workflow.add_edge("classification_node", "audit_node")

    # Define conditional routing
    workflow.add_conditional_edges(
        "audit_node",
        route_after_audit,
        {
            "interrogator_node": "interrogator_node",
            "assembly_node": "assembly_node"
        }
    )

    # Loop back from interrogator to audit
    # Actually, to prevent infinite loops in the test mock,
    # we'll route interrogator to assembly or END
    workflow.add_edge("interrogator_node", "assembly_node")""",
"""    # Add nodes
    workflow.add_node("ingestion_node", ingestion_node)
    workflow.add_node("classification_node", classification_node)
    workflow.add_node("audit_node", audit_node)
    workflow.add_node("interrogator_node", interrogator_node)
    workflow.add_node("assembly_node", assembly_node)
    workflow.add_node("update_node", update_node)

    # Set Entry Point conditionally based on state
    workflow.set_conditional_entry_point(
        route_entry,
        {
            "update_node": "update_node",
            "ingestion_node": "ingestion_node"
        }
    )

    # Define simple linear flow for early steps
    workflow.add_edge("ingestion_node", "classification_node")
    workflow.add_edge("classification_node", "audit_node")
    workflow.add_edge("update_node", "audit_node")

    # Define conditional routing
    workflow.add_conditional_edges(
        "audit_node",
        route_after_audit,
        {
            "interrogator_node": "interrogator_node",
            "assembly_node": "assembly_node"
        }
    )

    # Interrogator routes to END (pauses workflow for Laravel)
    workflow.add_edge("interrogator_node", END)""")

with open("src/core/workflow.py", "w") as f:
    f.write(content)
