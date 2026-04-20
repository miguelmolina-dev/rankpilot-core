# RankPilot System Architecture & Overview

## What is RankPilot?
RankPilot is an intelligent, agentic submission builder for legal directories such as **Legal 500** and **Chambers and Partners**. It uses Large Language Models (LLMs) orchestrated via **LangGraph** to automate the process of data extraction, schema validation, dynamic questioning for missing data (gap analysis), and the final assembly of submission documents (e.g., `.docx` files).

## Core Architecture
The system adopts a **completely stateless architecture** driven by a **FastAPI backend** and a **Laravel frontend**.
- **Stateless Operation:** The FastAPI server does not persist state across interactions. Instead, the Laravel frontend acts as the single source of truth. The frontend sends the entire `AgentState` (including history, user answers, and documents) in a JSON payload via the `/process` endpoint.
- **Workflow Orchestration:** **LangGraph** is used to orchestrate the state machine. Since there is no persistence, the workflow is designed to execute nodes, pause by reaching the `END` state when user input is needed (e.g., after generating a question in the `interrogator_node`), and resume execution appropriately based on the incoming state payload.
- **State Management:** The internal state for LangGraph (`AgentState`) is built using **Pydantic V2**. It enforces strict validation and typing to handle corrupted inputs gracefully (such as cleaning up PHP-specific formatting errors like empty `stdClass` objects).

## The LangGraph Workflow
The LangGraph state machine (`src/core/workflow.py`) defines a linear and conditional flow of execution:
1. **Entry Routing (`route_entry`):** Determines the starting point. If the payload contains a new user answer, the flow starts at the `process_answer_node`. Otherwise, for a new submission, it starts at the `classification_node`.
2. **`classification_node`:** Extracts text from raw base64-encoded documents (PDF/DOCX) and determines the `input_document_type`.
3. **`ingestion_node`:** Uses structured LLM outputs to autonomously map the extracted text into a target schema (e.g., `Legal500Submission` or `ChambersSubmission`) based on semantic meaning.
4. **`process_answer_node`:** When the user provides an answer to a previous question, this node updates the specific missing field in the Pydantic schema using the LLM.
5. **`sanitizer_node`:** Cleans and formats the extracted or updated data before validation.
6. **`audit_node`:** Performs gap analysis. It compares the current submission state against expected rules defined in configuration files (YAML/JSON in `configs/`). It identifies missing or incomplete fields and logs them as `gaps`.
7. **Audit Routing (`route_after_audit`):** If gaps are found, the workflow routes to the `interrogator_node`. If no gaps remain, it routes to the `assembly_node`.
8. **`interrogator_node`:** Formulates a precise, natural language question to ask the user for the missing data based on the identified gaps. After generating the question, the workflow ends and the state is sent back to the frontend.
9. **`assembly_node`:** Once the schema is completely populated, this node utilizes `docxtpl` (Jinja2 syntax) to inject the structured data into specific template `.docx` files. It outputs the assembled document as a base64 string for the frontend.

## Data Models and Schemas
The application strongly enforces the **Strategy Pattern** for handling different ranking directories.
- **Base Models:** Located in `src/core/schemas.py`, there is a base class `BaseSubmission` and specific models like `Legal500Submission` and `ChambersSubmission`. These Pydantic models contain extensive `Field(description="...")` annotations that provide context to the LLM during extraction and updating.
- **Strategies:** Located in `src/strategies/`, classes like `Legal500Strategy` and `ChambersStrategy` implement the specific logic for auditing (gap analysis) and assembly (document rendering) corresponding to their directory.

## Testing and Execution
- The backend API (`main.py`) acts as the entry point for production, running via Uvicorn/FastAPI.
- **Testing Scripts:**
  - `interactive_test.py`: Simulates the stateless frontend interactions, looping through questions and answers using a real HTTP cycle via `fastapi.testclient.TestClient`.
  - `local_workflow_test.py`: Directly invokes the LangGraph workflow bypassing the API to simulate processing and test node integrations directly.

## Configuration-Driven Behavior
Agent rules and behaviors (such as what fields are required, minimum word counts, etc.) are separated from Python code. They are defined in configuration files within the `configs/` directory (e.g., `legal500_us.yaml`). This adheres to the DRY principle and allows easy updates to ranking guidelines without changing core logic.
